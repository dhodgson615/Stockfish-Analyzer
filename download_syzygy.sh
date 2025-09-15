#!/bin/bash

# Create the directory if it doesn't exist
mkdir -p ~/chess/syzygy

# Download 3-4-5 piece tablebases from Lichess
cd ~/chess/syzygy

# Base URL for Lichess tablebase
BASE_URL="https://tablebase.lichess.ovh/tables/standard/3-4-5"

# List of all 3-4-5 piece tablebase files
FILES=(
    "K-v-K.rtbw" "K-v-K.rtbz"
    "KBN-v-K.rtbw" "KBN-v-K.rtbz"
    "KBP-v-K.rtbw" "KBP-v-K.rtbz"
    "KBP-v-KB.rtbw" "KBP-v-KB.rtbz"
    "KB-v-K.rtbw" "KB-v-K.rtbz"
    "KB-v-KB.rtbw" "KB-v-KB.rtbz"
    "KB-v-KN.rtbw" "KB-v-KN.rtbz"
    "KN-v-K.rtbw" "KN-v-K.rtbz"
    "KN-v-KN.rtbw" "KN-v-KN.rtbz"
    "KP-v-K.rtbw" "KP-v-K.rtbz"
    "KP-v-KP.rtbw" "KP-v-KP.rtbz"
    "KQ-v-K.rtbw" "KQ-v-K.rtbz"
    "KQ-v-KB.rtbw" "KQ-v-KB.rtbz"
    "KQ-v-KN.rtbw" "KQ-v-KN.rtbz"
    "KQ-v-KP.rtbw" "KQ-v-KP.rtbz"
    "KQ-v-KQ.rtbw" "KQ-v-KQ.rtbz"
    "KQ-v-KR.rtbw" "KQ-v-KR.rtbz"
    "KR-v-K.rtbw" "KR-v-K.rtbz"
    "KR-v-KB.rtbw" "KR-v-KB.rtbz"
    "KR-v-KN.rtbw" "KR-v-KN.rtbz"
    "KR-v-KP.rtbw" "KR-v-KP.rtbz"
    "KR-v-KR.rtbw" "KR-v-KR.rtbz"
)

# Download all files
for file in "${FILES[@]}"; do
    echo "Downloading $file..."
    curl -O "$BASE_URL/$file"
done

echo "Download complete. Tablebases installed in ~/chess/syzygy"

