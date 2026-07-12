const { buildModule } = require("@nomicfoundation/hardhat-ignition/modules");

module.exports = buildModule("SertifikatVerifikasiModule", (m) => {
  const sertifikatVerifikasi = m.contract("SertifikatVerifikasi");

  return { sertifikatVerifikasi };
});