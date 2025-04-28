import requests
import random
import logging
from time import sleep
from typing import List, Dict
from datetime import datetime
import json

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mira_waitlist_log.txt'),
        logging.StreamHandler()
    ]
)

class ProxyConfig:
    def __init__(self, proxy_string: str):
        """Parse proxy string in format ip:port:username:password"""
        try:
            ip, port, username, password = proxy_string.strip().split(':')
            self.ip = ip
            self.port = port
            self.username = username
            self.password = password
        except ValueError:
            raise ValueError(f"Invalid proxy format: {proxy_string}")

    def get_proxy_dict(self) -> Dict[str, str]:
        """Convert to requests proxy format"""
        proxy_auth = f"{self.username}:{self.password}@{self.ip}:{self.port}"
        return {
            'http': f'http://{proxy_auth}',
            'https': f'http://{proxy_auth}'
        }

class MiraWaitlistSubmitter:
    def __init__(self, proxy_file: str = 'proxies.txt'):
        self.headers = {
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.8',
            'content-type': 'application/json',
            'origin': 'https://flows.mira.network',
            'priority': 'u=1, i',
            'referer': 'https://flows.mira.network/',
            'sec-ch-ua': '"Brave";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        }
        
        self.occupations = [
            'Developer',
            'Product Manager',
            'Researcher',
            'Student',
            'Entrepreneur'
        ]
        
        self.url = 'https://flow-api.mira.network/v1/waitlist'
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.proxies = self.load_proxies(proxy_file)

    def load_proxies(self, filename: str) -> List[ProxyConfig]:
        """Load and parse proxies from file."""
        proxies = []
        try:
            with open(filename, 'r') as file:
                for line in file:
                    try:
                        proxy = ProxyConfig(line.strip())
                        proxies.append(proxy)
                    except ValueError as e:
                        logging.error(f"Error parsing proxy: {e}")
                        continue
            logging.info(f"Loaded {len(proxies)} proxies successfully")
            return proxies
        except FileNotFoundError:
            logging.error(f"Proxy file {filename} not found")
            return []

    def get_random_proxy(self) -> Dict[str, str]:
        """Get a random proxy from the list."""
        if not self.proxies:
            logging.warning("No proxies available, proceeding without proxy")
            return {}
        proxy_config = random.choice(self.proxies)
        proxy_dict = proxy_config.get_proxy_dict()
        return proxy_dict

    def load_emails(self, filename: str) -> List[str]:
        """Load email addresses from file."""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                emails = [line.strip() for line in file if line.strip()]
            logging.info(f"Loaded {len(emails)} email addresses")
            return emails
        except FileNotFoundError:
            logging.error(f"Email file {filename} not found")
            return []
        except Exception as e:
            logging.error(f"Error reading email file: {str(e)}")
            return []

    def get_random_occupation(self) -> str:
        """Get random occupation from list."""
        return random.choice(self.occupations)

    def check_response_success(self, response: requests.Response) -> bool:
        """Check if response indicates success."""
        try:
            response_data = response.json()
            return (response_data.get('success') is True and 
                    response_data.get('message') == 'Added to waitlist successfully')
        except json.JSONDecodeError:
            logging.error(f"Failed to parse JSON response: {response.text}")
            return False
        except Exception as e:
            logging.error(f"Error checking response: {str(e)}")
            return False

    def submit_email(self, email: str) -> bool:
        """Submit a single email address."""
        try:
            occupation = self.get_random_occupation()
            json_data = {
                'email': email,
                'occupation': occupation,
            }
            
            proxy = self.get_random_proxy()
            proxy_info = f"Using proxy: {list(proxy.values())[0]}" if proxy else "No proxy"
            logging.info(f"Submitting {email} with occupation {occupation}. {proxy_info}")
            
            response = self.session.post(
                self.url,
                json=json_data,
                proxies=proxy,
                timeout=30
            )
            
            if response.status_code == 200 and self.check_response_success(response):
                logging.info(f"Successfully added to waitlist: {email}")
                return True
            else:
                logging.warning(f"Failed to submit {email}. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except requests.RequestException as e:
            logging.error(f"Error submitting {email}: {str(e)}")
            return False

    def process_emails(self, email_file: str, delay_range: tuple = (2, 0)):
        """Process all email addresses from file."""
        emails = self.load_emails(email_file)
        if not emails:
            logging.error("No email addresses to process")
            return

        successful = 0
        failed = 0

        with open('results_mira.txt', 'w', encoding='utf-8') as results_file:
            for i, email in enumerate(emails, 1):
                logging.info(f"Processing email {i}/{len(emails)}: {email}")
                
                if self.submit_email(email):
                    successful += 1
                    results_file.write(f"{email}: SUCCESS\n")
                else:
                    failed += 1
                    results_file.write(f"{email}: FAILED\n")
                results_file.flush()
                
                if i < len(emails):
                    sleep_time = random.uniform(*delay_range)
                    logging.info(f"Waiting {sleep_time:.2f} seconds before next email...")
                    sleep(sleep_time)

        logging.info(f"Processing completed. Successful: {successful}, Failed: {failed}")
        logging.info(f"Results saved to results_mira.txt")

def main():
    submitter = MiraWaitlistSubmitter(proxy_file='proxies.txt')
    submitter.process_emails('emails.txt')

if __name__ == "__main__":
    main()
