#!/usr/bin/env python3
"""
Instagram Reel Downloader
GitHub Actions workflow runner
Downloads reels using yt-dlp and uploads to Telegram
"""

import os
import sys
import json
import subprocess
import requests
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReelDownloader:
    """Main downloader class"""

    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.reel_url = os.getenv('REEL_URL')
        self.chat_id = os.getenv('CHAT_ID')
        self.user_id = os.getenv('USER_ID')
        self.message_id = os.getenv('MESSAGE_ID')
        self.job_id = os.getenv('JOB_ID', 'unknown')

        self.temp_dir = Path('/tmp/instagram-downloads')
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self.validate_inputs()

    def validate_inputs(self):
        """Validate environment variables"""
        required = ['BOT_TOKEN', 'REEL_URL', 'CHAT_ID', 'USER_ID', 'MESSAGE_ID']

        for var in required:
            if not os.getenv(var):
                raise ValueError(f'Missing environment variable: {var}')

        logger.info(f'[{self.job_id}] Inputs validated')

    def download_reel(self):
        """Download reel using yt-dlp"""
        try:
            logger.info(f'[{self.job_id}] Starting download: {self.reel_url}')

            output_template = str(self.temp_dir / '%(id)s.%(ext)s')

            command = [
                'yt-dlp',
                '--format', 'best[ext=mp4]',
                '--output', output_template,
                '--quiet',
                '--no-warnings',
                '--socket-timeout', '30',
                self.reel_url,
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                raise Exception(f'yt-dlp failed: {result.stderr}')

            # Find downloaded file
            mp4_files = list(self.temp_dir.glob('*.mp4'))

            if not mp4_files:
                raise Exception('No MP4 file downloaded')

            downloaded_file = mp4_files[0]

            logger.info(f'[{self.job_id}] Downloaded: {downloaded_file}')

            return str(downloaded_file)

        except subprocess.TimeoutExpired:
            raise Exception('Download timeout (exceeded 120 seconds)')
        except Exception as error:
            logger.error(f'[{self.job_id}] Download failed: {str(error)}')
            raise

    def upload_to_telegram(self, video_path):
        """Upload video to Telegram"""
        try:
            logger.info(f'[{self.job_id}] Uploading to Telegram')

            url = f'https://api.telegram.org/bot{self.bot_token}/sendVideo'

            with open(video_path, 'rb') as video_file:
                files = {'video': video_file}
                data = {
                    'chat_id': self.chat_id,
                    'caption': '✅ Instagram Reel',
                    'parse_mode': 'HTML',
                    'reply_to_message_id': self.message_id,
                }

                response = requests.post(url, files=files, data=data, timeout=300)

                if response.status_code != 200:
                    error_text = response.text
                    raise Exception(f'Telegram API error: {error_text}')

                logger.info(f'[{self.job_id}] Successfully uploaded to Telegram')
                return response.json()

        except Exception as error:
            logger.error(f'[{self.job_id}] Upload failed: {str(error)}')
            raise

    def notify_error(self, error_message):
        """Send error notification to Telegram"""
        try:
            url = f'https://api.telegram.org/bot{self.bot_token}/sendMessage'

            message = f'❌ <b>Download failed</b>\n\n<code>{error_message}</code>'

            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'reply_to_message_id': self.message_id,
            }

            response = requests.post(url, json=data, timeout=30)

            if response.status_code == 200:
                logger.info(f'[{self.job_id}] Error notification sent')

        except Exception as error:
            logger.error(f'[{self.job_id}] Failed to send error notification: {error}')

    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil

            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info(f'[{self.job_id}] Cleaned up temporary files')

        except Exception as error:
            logger.error(f'[{self.job_id}] Cleanup failed: {error}')

    def run(self):
        """Execute the download workflow"""
        try:
            logger.info(f'[{self.job_id}] Starting Instagram Reel download')
            logger.info(f'[{self.job_id}] URL: {self.reel_url}')

            # Download
            video_path = self.download_reel()

            # Upload
            self.upload_to_telegram(video_path)

            logger.info(f'[{self.job_id}] Download workflow completed successfully')
            return 0

        except Exception as error:
            logger.error(f'[{self.job_id}] Workflow failed: {str(error)}')
            self.notify_error(str(error))
            return 1

        finally:
            self.cleanup()


def main():
    """Main entry point"""
    try:
        downloader = ReelDownloader()
        exit_code = downloader.run()
        sys.exit(exit_code)

    except Exception as error:
        logger.error(f'Fatal error: {str(error)}')
        sys.exit(1)


if __name__ == '__main__':
    main()
