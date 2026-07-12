const hre = require("hardhat");

async function main() {
  const SertifikatVerifikasi = await hre.ethers.getContractFactory("SertifikatVerifikasi");
  const contract = await SertifikatVerifikasi.deploy();
  await contract.waitForDeployment();
  
  console.log("✅ Contract deployed to:", await contract.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});