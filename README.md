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

---

## future roadmap

1. [ ] рефакторинг syncworker:
   1. [ ] определить позитивный сценарий, шаги, транзакции
   2. [ ] места ошибок, сценарии их обработки
   3. [ ] саммари прогона(в файл, в терминал, в жопу - определить куда)
2. [ ] дока
   1. [ ] как поднять
   2. [ ] общий сценарий, компоненты
   3. [ ] описание конфигов
   4. [ ] faq проблем
3. [ ] логирование
   1. [ ] единый формат логов, разбивка по INFO/WARN/ERROR
   2. [ ] логи причин почему трек не скачался
   3. [ ] логи крупных шагов, для удобной ориентации по логам
4. [ ] дашборд
   1. [ ] healthcheck
   2. [ ] логи+ошибки последнего прогона - lastrun.json
   3. [ ] список не скачанных треков
5. [ ] dry-run
6. [ ] раскатка изменений
