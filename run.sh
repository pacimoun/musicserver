#!/bin/bash

cd "$(dirname "$0")"

if [ -z "$1" ]; then
    echo "🎵 Управление сервером (Navidrome + Sync)"
    echo "Использование: ./run.sh [команда]"
    echo ""
    echo "Команды:"
    echo "  build       Пересобрать и запустить контейнеры"
    echo "  sync        Запустить синхронизацию"
    echo "  logs        Смотреть логи воркера (в реальном времени)"
    echo "  down        Остановить контейнеры"
    exit 0
fi

COMMAND=$1
shift

case "$COMMAND" in
    build)
        echo "🏗️ Пересборка контейнеров"
        docker compose up -d --build
        ;;
    
    sync)
        echo "🔄 Запуск ручной синхронизации"
        docker compose exec sync-worker /app/scripts/full_sync.sh "$@"
        ;;
        
    logs)
        echo "📜 Логи sync-worker (Ctrl+C для выхода)"
        docker compose logs -f sync-worker
        ;;
        
    down)
        echo "🛑 Остановка контейнеров"
        docker compose down
        ;;
        
    *)
        echo "❌ Неизвестная команда: $COMMAND"
        echo "Запусти run.sh для списка команд."
        exit 1
        ;;
esac