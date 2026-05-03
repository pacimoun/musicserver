#!/bin/bash
set -e

echo "=== Подготовка для развертывания Navidrome ==="

echo "[1/4] Установка Git"
sudo apt-get update
sudo apt-get install -y git curl

if ! command -v docker &> /dev/null; then
    echo "[2/4] Установка Docker"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "Docker установлен."
else
    echo "[2/4] Docker уже установлен"
fi

echo "[3/4] Загрузка репозитория"
REPO_URL="https://github.com/pacimoun/musicserver.git"
REPO_NAME=$(basename "$REPO_URL" .git)

if [ ! -d "$REPO_NAME" ]; then
    if ! git clone "$REPO_URL"; then
        echo "❌ Ошибка при клонировании"
        rm -rf "$REPO_NAME" 
        exit 1
    fi
else
    echo "Папка $REPO_NAME уже существует"
fi

cd "$REPO_NAME"
chmod +x setup.sh

sudo usermod -aG docker $USER

echo "================================================="
echo "Все установили"
echo "Чтобы развернуть сервер:"
echo "1. Перейди в проект cd $REPO_NAME"
echo "2. Примени права группы: newgrp docker"
echo "3. Скопируй конфиг: cp .env.example .env"
echo "4. Заполни секреты: nano .env"
echo "5. Запусти сервер: ./setup.sh"
echo "================================================="
