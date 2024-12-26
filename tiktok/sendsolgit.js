require('dotenv').config();
const fs = require('fs');
const bs58 = require("bs58");
const fetch = require('node-fetch');
const {
  Connection,
  Keypair,
  PublicKey,
  Transaction,
  sendAndConfirmTransaction,
} = require("@solana/web3.js");
const {
  getAssociatedTokenAddress,
  createAssociatedTokenAccountInstruction,
  createTransferInstruction,
  TOKEN_PROGRAM_ID,
  ASSOCIATED_TOKEN_PROGRAM_ID,
} = require("@solana/spl-token");

const API_KEY = process.env.TIKTOK_API_KEY;
const VIDEO_ID = process.env.TIKTOK_VIDEO_ID;
const SEARCH_PHRASE = process.env.SEARCH_PHRASE || "pencil";
const LEA_TO_SEND = parseInt(process.env.LEA_TO_SEND || "30000", 10);
const NUMBER_OF_WINNERS = parseInt(process.env.NUMBER_OF_WINNERS || "2", 10);
const SOLANA_PRIVATE_KEY = process.env.SOLANA_PRIVATE_KEY;
const TOKEN_MINT_ADDRESS = process.env.TOKEN_MINT_ADDRESS;

const successfulTransfers = new Set();
let jsonLog = {
  timestamp: new Date().toISOString(),
  video_id: VIDEO_ID,
  search_phrase: SEARCH_PHRASE,
  events: [],
  comments: [],
  winners: [],
  statistics: {},
  errors: []
};
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

function logEvent(type, message, data = null) {
  const event = {
    timestamp: new Date().toISOString(),
    type: type,
    message: message,
    data: data
  };
  jsonLog.events.push(event);
  console.log(`${type}: ${message}`);
  saveJsonLog();
}

function saveJsonLog() {
  try {
    fs.writeFileSync('answers.json', JSON.stringify(jsonLog, null, 2));
  } catch (error) {
    console.error('Error saving JSON log:', error);
  }
}

function isSolanaAddress(address) {
  if (typeof address !== 'string' || address.length !== 44) {
    return false;
  }
  const base58Regex = /^[1-9A-HJ-NP-Za-km-z]+$/;
  return base58Regex.test(address);
}

function extractSolanaAddresses(text) {
  const words = text.split(/\s+/);
  return words.filter(word => isSolanaAddress(word));
}

function isValidComment(comment) {
  const hasKeyword = comment.toLowerCase().includes(SEARCH_PHRASE.toLowerCase());
  const solanaAddresses = extractSolanaAddresses(comment);
  if (hasKeyword && solanaAddresses.length === 1) {
    logEvent('VALIDATION', 'Found exactly one valid Solana address', solanaAddresses[0]);
    return solanaAddresses[0];
  }
  return null;
}

async function getComments() {
  try {
    logEvent('FETCH', 'Fetching comments for video', { video_id: VIDEO_ID });
    const response = await fetch(
      `https://api.ayrshare.com/api/comments/${VIDEO_ID}?platform=tiktok&searchPlatformId=true`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${API_KEY}`,
          'Content-Type': 'application/json'
        }
      }
    );
    const data = await response.json();
    logEvent('FETCH', 'TikTok API Response received', data);
    if (!data.tiktok) {
      logEvent('FETCH', 'No TikTok comments found');
      return [];
    }
    jsonLog.comments = data.tiktok;
    return data.tiktok;
  } catch (error) {
    logEvent('ERROR', 'Error while fetching TikTok comments', error.message);
    return [];
  }
}

const pendingTransfers = new Map();

async function sendTokensToWinnerWithRetry(recipientAddress, maxRetries = 5) {
  if (successfulTransfers.has(recipientAddress)) {
    logEvent('TRANSFER', 'Skipping duplicate transfer - already successful', { address: recipientAddress });
    return true;
  }
  if (pendingTransfers.has(recipientAddress)) {
    logEvent('TRANSFER', 'Skipping duplicate transfer - already pending', { address: recipientAddress });
    return false;
  }
  pendingTransfers.set(recipientAddress, Date.now());
  let attempt = 0;
  let lastError = null;
  try {
    while (attempt < maxRetries) {
      try {
        attempt++;
        logEvent('TRANSFER', `Attempt ${attempt}/${maxRetries} to send tokens to ${recipientAddress}`);
        const senderSecretKey = bs58.decode(SOLANA_PRIVATE_KEY);
        const senderKeypair = Keypair.fromSecretKey(senderSecretKey);
        const connection = new Connection("https://api.mainnet-beta.solana.com", "confirmed");
        const recipientPublicKey = new PublicKey(recipientAddress);
        const tokenMintAddress = new PublicKey(TOKEN_MINT_ADDRESS);
        if (successfulTransfers.has(recipientAddress)) {
          logEvent('TRANSFER', 'Transfer was completed by another attempt', { address: recipientAddress });
          return true;
        }
        const senderTokenAccount = await getAssociatedTokenAddress(
          tokenMintAddress,
          senderKeypair.publicKey,
          false,
          TOKEN_PROGRAM_ID,
          ASSOCIATED_TOKEN_PROGRAM_ID
        );
        const recipientTokenAccount = await getAssociatedTokenAddress(
          tokenMintAddress,
          recipientPublicKey,
          false,
          TOKEN_PROGRAM_ID,
          ASSOCIATED_TOKEN_PROGRAM_ID
        );
        const recipientAccountInfo = await connection.getAccountInfo(recipientTokenAccount);
        if (!recipientAccountInfo) {
          logEvent('TRANSFER', 'Creating token account for winner');
          const createAccountTransaction = new Transaction().add(
            createAssociatedTokenAccountInstruction(
              senderKeypair.publicKey,
              recipientTokenAccount,
              recipientPublicKey,
              tokenMintAddress,
              TOKEN_PROGRAM_ID,
              ASSOCIATED_TOKEN_PROGRAM_ID
            )
          );
          await sendAndConfirmTransaction(connection, createAccountTransaction, [senderKeypair]);
          await sleep(2000);
        }
        const amountToSend = LEA_TO_SEND * 10 ** 6;
        const transferTransaction = new Transaction().add(
          createTransferInstruction(
            senderTokenAccount,
            recipientTokenAccount,
            senderKeypair.publicKey,
            amountToSend,
            [],
            TOKEN_PROGRAM_ID
          )
        );
        const signature = await sendAndConfirmTransaction(connection, transferTransaction, [senderKeypair]);
        successfulTransfers.add(recipientAddress);
        pendingTransfers.delete(recipientAddress);
        logEvent('TRANSFER', 'Transfer successful', {
          attempt,
          amount: LEA_TO_SEND,
          recipient: recipientAddress,
          signature: signature
        });
        return true;
      } catch (error) {
        lastError = error;
        logEvent('ERROR', `Transfer attempt ${attempt} failed`, error.message);
        if (attempt < maxRetries) {
          const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
          logEvent('RETRY', `Waiting ${delay}ms before retry`);
          await sleep(delay);
        }
      }
    }
    logEvent('ERROR', `All ${maxRetries} transfer attempts failed`, lastError.message);
    return false;
  } finally {
    pendingTransfers.delete(recipientAddress);
  }
}

async function replyToComment(commentId, solanaAddress, username, signature) {
  try {
    const customReply = `You won ! Tx : ${signature}`;
    logEvent('REPLY', 'Sending winner notification', { username, address: solanaAddress });
    const response = await fetch(
      `https://api.ayrshare.com/api/comments/reply/${commentId}`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${API_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          platforms: ['tiktok'],
          comment: customReply,
          searchPlatformId: true,
          videoId: VIDEO_ID
        })
      }
    );
    const data = await response.json();
    logEvent('REPLY', 'Winner notification sent', data);
    return true;
  } catch (error) {
    logEvent('ERROR', 'Error sending winner notification', error.message);
    return false;
  }
}

async function processWinner(username, data) {
  logEvent('PROCESSING', `Processing winner ${username}`, { address: data.address });
  const success = await sendTokensToWinnerWithRetry(data.address);
  if (success) {
    try {
      const signature = jsonLog.events[jsonLog.events.length - 1].data.signature;
      await replyToComment(data.commentId, data.address, username, signature);
      jsonLog.winners.push({
        username,
        address: data.address,
        commentId: data.commentId,
        timestamp: new Date().toISOString()
      });
      return true;
    } catch (error) {
      logEvent('ERROR', 'Failed to send notification, but tokens were sent', error.message);
      return true;
    }
  }
  return false;
}

async function processWinners(winners) {
  for (const [username, data] of winners) {
    let winnerProcessed = false;
    let retryCount = 0;
    const maxRetries = 3;
    while (!winnerProcessed && retryCount < maxRetries) {
      retryCount++;
      winnerProcessed = await processWinner(username, data);
      if (!winnerProcessed && retryCount < maxRetries) {
        const delay = 5000 * retryCount;
        logEvent('RETRY', `Waiting ${delay}ms before retrying winner processing`);
        await sleep(delay);
      }
    }
    if (!winnerProcessed) {
      logEvent('ERROR', `Failed to process winner ${username} after all attempts`);
    }
  }
}

async function selectWinnersAndSendTokens(validComments) {
  const uniqueUsers = new Map();
  const uniqueWallets = new Map();
  const duplicateWallets = new Set();
  validComments.forEach(comment => {
    const address = isValidComment(comment.comment);
    if (address) {
      const username = comment.username;
      const timestamp = new Date(comment.created).getTime();
      if (uniqueWallets.has(address)) {
        const existingEntry = uniqueWallets.get(address);
        duplicateWallets.add(address);
        logEvent('DUPLICATE', 'Wallet used multiple times', {
          wallet: address,
          previousUser: existingEntry.username,
          currentUser: username
        });
        if (uniqueUsers.has(existingEntry.username)) {
          uniqueUsers.delete(existingEntry.username);
        }
        return;
      }
      if (uniqueUsers.has(username)) {
        const existingEntry = uniqueUsers.get(username);
        if (timestamp > existingEntry.timestamp) {
          uniqueWallets.delete(existingEntry.address);
          uniqueUsers.set(username, {
            address,
            commentId: comment.commentId,
            timestamp
          });
          uniqueWallets.set(address, {
            username,
            commentId: comment.commentId,
            timestamp
          });
        }
      } else {
        uniqueUsers.set(username, {
          address,
          commentId: comment.commentId,
          timestamp
        });
        uniqueWallets.set(address, {
          username,
          commentId: comment.commentId,
          timestamp
        });
      }
    }
  });
  jsonLog.statistics = {
    totalComments: validComments.length,
    uniqueParticipants: uniqueUsers.size,
    uniqueWallets: uniqueWallets.size,
    duplicateWallets: duplicateWallets.size
  };
  const userArray = Array.from(uniqueUsers.entries());
  for (let i = userArray.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [userArray[i], userArray[j]] = [userArray[j], userArray[i]];
  }
  const winners = userArray.slice(0, NUMBER_OF_WINNERS);
  logEvent('WINNERS', `Selected ${winners.length} winners`, winners);
  await processWinners(winners);
}

async function processCommentsAndRewardWinners() {
  try {
    logEvent('START', 'Starting comment verification and winner selection');
    const comments = await getComments();
    if (comments.length > 0) {
      await selectWinnersAndSendTokens(comments);
    }
    logEvent('COMPLETE', 'Processing completed');
  } catch (error) {
    logEvent('ERROR', 'Error in main process', error.message);
  }
}

logEvent('INIT', 'Starting TikTok Solana game');
processCommentsAndRewardWinners();
