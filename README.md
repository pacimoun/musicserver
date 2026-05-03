# Нишевый мьюзик соса бэйби сервер (Navidrome + SoundCloud) 

Docker-контейнеры:
1. **Navidrome** - стриминговый сервер
2. **Sync-Worker** - среда с утилитами и скриптами для регулярной синхронизации библиотеки с sc

---

## Требования к хосту

* если сервер разворачивается на Windows, то нужно установить и подготовить WSL2 (Debian)

---

## Подготовка окружения Windows (WSL2)

> Этот шаг нужен **только** если хост на Windows. При развертывании на Linux сервере можно скипнуть.

### 1. Конфигурация ресурсов и сети
Чтобы не жрало ресурсы нужно задать лимиты
Создай файл `.wslconfig` в (`C:\Users\USERNAME\.wslconfig`):

```ini
[wsl2]
memory=8GB
processors=6
swap=2GB
autoMemoryReclaim=dropcache
networkingMode=mirrored
localhostForwarding=true
```
Режим `networkingMode=mirrored` важен, если на пк поднят VPN, и необходимо пробрасывать эти настройки внутрь WSL для корректного исходящего подключения

### 2. Проброс портов
Для доступа к серверу из локальной сети пробрось порт из Windows в WSL2

Запусти PowerShell от админа и выполни:
```powershell
netsh interface portproxy add v4tov4 listenport={ND_PORT} listenaddress=0.0.0.0 connectport={ND_PORT} connectaddress=127.0.0.1
```

### 3. Настройка Брандмауэра Windows
Разрешаем входящие подключения для порта {ND_PORT} 
Зайди в **Windows Defender Firewall with Advanced Security** -> **Inbound Rules** -> **Add rule** 
Параметры:
* **Rule type:** Port
* **Protocol:** TCP
* **Specific rule ports:** {ND_PORT}
* **Action:** Allow the connection
* **Profiles:** All (Domain, Private, Public)
* **Name:** navidrome

### 4. Настройка V2RayN
Если для впна юзается V2RayN то:
**Settings** -> **Option Settings** -> **Core: basic settings**
И поставить галочку в **Allow connections from the LAN**

---

## Установка и развертывание

```bash
bash <(curl -s https://gist.githubusercontent.com/pacimoun/fbaa8805300f8384449b45c3dd8a5b34/raw/1af59e091ae985d107b72aaab17dcc516c653256/bootstrap.sh)
```

или

```bash
wget -qO- https://gist.githubusercontent.com/pacimoun/fbaa8805300f8384449b45c3dd8a5b34/raw/1af59e091ae985d107b72aaab17dcc516c653256/bootstrap.sh | bash
```


**После установки:**
```bash
id -u # Убедится что выводится 1000, если нет - фикси
newgrp docker # Применение прав группы, что Docker работал без sudo
cd musicserver
cp .env.example .env
nano .env   # Заполни свои данные
./setup.sh
```

---

## Настройка доступа из интернета

Для доступа также нужно пробросить порт {ND_PORT} на роутере

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
