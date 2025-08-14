#!/usr/bin/with-contenv bashio

bashio::log.info "Pull-Up Bot запускається..."

BOT_TOKEN=$(bashio::config 'bot_token')
GUILD_ID=$(bashio::config 'guild_id')
CHANNEL_ID=$(bashio::config 'channel_id')

# Тут виклик вашого бота
python3 /pull_up/bot.py --token "$BOT_TOKEN" --guild "$GUILD_ID" --channel "$CHANNEL_ID"
