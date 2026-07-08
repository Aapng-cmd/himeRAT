# Агент инвентаризации узла (лаборатория)

См. корневой [README.md](../README.md).

## Запуск

```bash
pip install -r requirements.txt
python stage1/run.py --server http://СЕРВЕР:1337
```

Агент внешне выглядит как клиент синхронизации `InventorySync/1.2`. Все операции идут через зашифрованный канал ECDH + AES-GCM.
