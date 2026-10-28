require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config({ path: "../.env" });

// PRIVATE_KEY hanya dibutuhkan saat deploy ke Sepolia.
// Untuk "npx hardhat test" (jaringan lokal) variabel ini boleh kosong.
const accounts = process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [];

module.exports = {
  solidity: "0.8.28",
  paths: {
    sources: "./smart-contract/contracts",
    tests: "./smart-contract/test",
    cache: "./smart-contract/cache",
    artifacts: "./smart-contract/artifacts",
    ignition: "./smart-contract/ignition",
  },
  networks: {
    sepolia: { url: process.env.SEPOLIA_RPC_URL || "", accounts },
  },
  gasReporter: { enabled: process.env.REPORT_GAS === "1", currency: "USD" },
};
