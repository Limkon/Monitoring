name: Send Telegram Message

on:
   schedule:
   - cron: '5 * */10 * *'
   workflow_dispatch:
    inputs:
      branch:
        description: 'Branch to run the workflow on'
        required: true
        default: 'main'

jobs:
  send-message:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8

      - name: Install Dependencies
        run: |
          pip install requests

      - name: Build web
        run: python ./tools/webtelegram.py
