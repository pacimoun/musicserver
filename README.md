# Нишевый соса мьюзик бэйби сервер (Navidrome + SoundCloud)

## Docker-контейнеры:
1. **navidrome** - стриминговый сервер
2. **syncworker** - среда с утилитами и скриптами для регулярной синхронизации библиотеки с sc

---

## Требования к хосту

* linux
* git, curl

---

## Установка и развертывание

```bash
bash <(curl -s https://gist.githubusercontent.com/pacimoun/fbaa8805300f8384449b45c3dd8a5b34/raw/201d133e283fb4ccb66d0fdbd5153095c5d4e7b8/bootstrap.sh)
```


**После установки:**
```bash
id -u # убедится что выводится 1000, если нет - фикси падла
newgrp docker # применение прав группы, чтобы Docker работал без sudo
cd musicserver
cp .env.example .env
nano .env   # Заполни свои данные
./setup.sh
```

---

## Настройка доступа из интернета

Для доступа также нужно пробросить порт {ND_PORT} (по дефолту 4533) на роутере

Если роутер на OpenWRT, проброс можно настроить через LuCI (раздел *Network -> Firewall -> Port Forwards*) или по SSH:

```bash
uci add firewall redirect
uci set firewall.@redirect[-1].name='Navidrome_WAN'
uci set firewall.@redirect[-1].src='wan'
uci set firewall.@redirect[-1].src_dport='{ND_PORT}'
uci set firewall.@redirect[-1].dest='lan'
uci set firewall.@redirect[-1].dest_ip='SERVER_LOCAL_IP'
uci set firewall.@redirect[-1].dest_port='{ND_PORT}'
uci set firewall.@redirect[-1].target='DNAT'
uci commit firewall
/etc/init.d/firewall restart
```

---

## Использование и управление

Интерфейс Navidrome будет доступен по адресу: `http://localhost:{ND_PORT}`

Синхронизация происходит каждые 7 дней.
**Для ручного управления проектом**:

```bash
./run.sh
```

При `./run.sh sync` воркер сначала скачивает полные версии из SoundCloud.
Для отсутствующих файлов он ищет ту же запись в локальной библиотеке, на Zaycev,
Bandcamp, Lmusic, Muzoi и среди других загрузок SoundCloud. Перед импортом воркер
проверяет название, исполнителя и длительность аудио. Файл сохраняется
с ID исходного трека SoundCloud, поэтому он попадает в нужные лайки и плейлисты.
Строки с `!` в журнале перечисляют треки, для которых пока не найдена полная версия.

---

## future roadmap

1. [ ] рефакторинг syncworker:
   1. [ ] места ошибок, сценарии их обработки
   2. [ ] саммари прогона(в файл, в терминал, в жопу - определить куда)
2. [ ] логирование
   1. [ ] логи причин почему трек не скачался
3. [ ] дашборд
   1. [ ] логи+ошибки последнего прогона - lastrun.json
   2. [ ] список не скачанных треков
4. [ ] dry-run
