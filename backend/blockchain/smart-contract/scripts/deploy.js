// Deploy SertifikatVerifikasi (versi revisi F02) ke jaringan yang dipilih.
// Jalankan dari folder backend/blockchain:
//   npx hardhat compile
//   npx hardhat test
//   npx hardhat run smart-contract/scripts/deploy.js --network sepolia
const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const saldo = await hre.ethers.provider.getBalance(deployer.address);
  console.log("Wallet deployer (akan menjadi ADMIN kontrak):", deployer.address);
  console.log("Saldo:", hre.ethers.formatEther(saldo), "ETH");

  const Kontrak = await hre.ethers.getContractFactory("SertifikatVerifikasi");
  const kontrak = await Kontrak.deploy();
  const tx = kontrak.deploymentTransaction();
  console.log("Tx deploy:", tx.hash, "(menunggu konfirmasi...)");
  await kontrak.waitForDeployment();
  const rc = await tx.wait();

  const alamat = await kontrak.getAddress();
  console.log("\n✅ Kontrak ter-deploy di :", alamat);
  console.log("   Blok                 :", rc.blockNumber);
  console.log("   Gas deploy           :", rc.gasUsed.toString());
  console.log("   Admin kontrak        :", await kontrak.admin());
  console.log("\nLangkah berikutnya:");
  console.log(`  1) backend/.env           -> CONTRACT_ADDRESS=${alamat}`);
  console.log(`  2) frontend (.env / Cloudflare Pages) -> VITE_CONTRACT_ADDRESS=${alamat}`);
  console.log(`  3) Etherscan: https://sepolia.etherscan.io/address/${alamat}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
