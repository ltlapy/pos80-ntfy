## 이게뭐야
ntfy.sh에서 알림을 끌어다가 프린터에 쏩니다.

### TODO
- [ ] ~~가독성을 어떻게든~~

## how to run
```sh
cp example.env .env
vi .env
# edit some environments...
./run.sh
```
or
```sh
# Start manually
export $(grep -v '^#' .env | xargs)
run

# unset environments
# https://stackoverflow.com/a/20909045
unset $(grep -v '^#' .env | sed -E 's/(.*)=.*/\1/' | xargs)
```