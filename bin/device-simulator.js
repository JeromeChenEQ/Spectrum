/*
  Device simulator for local testing.
  Usage: node bin/device-simulator.js <boxId> <wavPath>
*/

const fs = require("fs");
const path = require("path");

async function run() {
  const boxId = process.argv[2];
  const wavPath = process.argv[3];

  if (!boxId || !wavPath) {
    console.error("Usage: node bin/device-simulator.js <boxId> <wavPath>");
    process.exit(1);
  }

  const absolutePath = path.resolve(wavPath);
  const fileBuffer = fs.readFileSync(absolutePath);

  const formData = new FormData();
  formData.append("box_id", boxId);
  formData.append("audio_file", new Blob([fileBuffer], { type: "audio/wav" }), path.basename(absolutePath));

  const response = await fetch("http://localhost:8000/api/v1/alerts/from-device", {
    method: "POST",
    body: formData
  });

  const payload = await response.json();
  console.log(payload);
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});