/**
 * Cloudflare Worker Entry Point
 * Main handler for Telegram webhooks
 */

import { getConfig, validateConfig } from './config.js';
import { parseTelegramUpdate, validateWorkflowPayload } from './validators.js';
import { processInstagramUrl, createDownloadTask } from './instagram.js';
import {
  notifyInvalidUrl,
  notifyDownloadStarted,
  notifyDownloadError,
  telegramApiCall,
} from './telegram.js';
import { triggerWorkflow, buildWorkflowTrigger } from './github.js';

/**
 * Main request handler
 */
export default {
  async fetch(request, env, ctx) {
    // Initialize configuration
    let config;

    try {
      config = getConfig(env);
      validateConfig(config);
    } catch (error) {
      console.error('Configuration error:', error.message);
      return new Response(JSON.stringify({ error: 'Configuration error' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Route requests
    const url = new URL(request.url);
    const path = url.pathname;

    try {
      if (path === '/webhook' && request.method === 'POST') {
        return await handleWebhook(request, config, ctx);
      }

      if (path === '/health' && request.method === 'GET') {
        return handleHealth();
      }

      return new Response(JSON.stringify({ error: 'Not found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      });
    } catch (error) {
      console.error('Request error:', error);
      return new Response(JSON.stringify({ error: 'Internal server error' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
    }
  },
};

/**
 * Handle Telegram webhook
 */
async function handleWebhook(request, config, ctx) {
  try {
    const update = await request.json();

    if (!update || typeof update !== 'object') {
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Parse the update
    const parsed = parseTelegramUpdate(update);

    if (!parsed) {
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Only handle text messages
    if (parsed.type !== 'message' || !parsed.text) {
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Process the message asynchronously
    ctx.waitUntil(processMessage(parsed, config));

    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('Webhook processing error:', error);
    return new Response(JSON.stringify({ ok: false }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

/**
 * Process incoming message
 */
async function processMessage(parsed, config) {
  const { chatId, userId, text, messageId } = parsed;

  try {
    // Extract URL from message
    const urlMatch = text.match(/(https?:\/\/[^\s]+)/);

    if (!urlMatch) {
      await notifyInvalidUrl(chatId, messageId, config.botToken);
      return;
    }

    const url = urlMatch[1];

    // Validate Instagram URL
    const validation = processInstagramUrl(url);

    if (!validation.valid) {
      await notifyInvalidUrl(chatId, messageId, config.botToken);
      return;
    }

    // Create download task
    const task = createDownloadTask(url, chatId, userId, messageId);

    if (task.status === 'failed') {
      await notifyDownloadError(chatId, messageId, task.error, config.botToken);
      return;
    }

    // Send download started notification
    await notifyDownloadStarted(chatId, config.botToken);

    // Build workflow trigger payload
    const workflowPayload = buildWorkflowTrigger(
      validation.cleanUrl,
      chatId,
      userId,
      messageId,
      task.jobId
    );

    // Validate payload
    const payloadValidation = validateWorkflowPayload(workflowPayload);

    if (!payloadValidation.valid) {
      await notifyDownloadError(
        chatId,
        messageId,
        payloadValidation.error,
        config.botToken
      );
      return;
    }

    // Trigger GitHub Actions workflow
    await triggerWorkflow(config, workflowPayload);

    // Log successful trigger
    console.log(`[${task.jobId}] Workflow triggered for reel: ${validation.reelId}`);
  } catch (error) {
    console.error('Message processing error:', error);

    try {
      await notifyDownloadError(
        chatId,
        messageId,
        'An unexpected error occurred. Please try again.',
        config.botToken
      );
    } catch (notifyError) {
      console.error('Failed to send error notification:', notifyError);
    }
  }
}

/**
 * Health check endpoint
 */
function handleHealth() {
  return new Response(JSON.stringify({
    status: 'healthy',
    timestamp: new Date().toISOString(),
  }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}
