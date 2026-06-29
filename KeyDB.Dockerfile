FROM eqalpha/keydb:latest
CMD ["keydb-server", "--threads", "4", "--protected-mode", "no"]
