#!/bin/sh
# Rebuild the broker video from film.html — one command, no dependencies
# beyond Chrome. Output: ~/Desktop/guard-feedback-video.mp4
cd "$(dirname "$0")"
python3 save_server.py & SRV=$!
sleep 1
rm -f guard-feedback.mp4 film.err
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --no-first-run --user-data-dir=/tmp/chrome-film-run \
  "http://127.0.0.1:8777/film.html" >/dev/null 2>&1 & CHROME=$!
echo "rendering (about 2 minutes)…"
n=0; until [ -s guard-feedback.mp4 ] || [ -s film.err ]; do sleep 5; n=$((n+1)); [ $n -gt 60 ] && break; done
kill $CHROME $SRV 2>/dev/null
[ -s film.err ] && { echo "RENDER ERROR:"; cat film.err; exit 1; }
cp guard-feedback.mp4 ~/Desktop/guard-feedback-video.mp4
echo "done → ~/Desktop/guard-feedback-video.mp4"
