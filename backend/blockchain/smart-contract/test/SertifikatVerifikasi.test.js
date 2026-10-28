// Pengujian unit smart contract SertifikatVerifikasi
// Jalankan:  npx hardhat test        (laporan gas: REPORT_GAS=1 npx hardhat test)
const { expect } = require("chai");
const { ethers } = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-toolbox/network-helpers");

describe("SertifikatVerifikasi", function () {
  async function deployFixture() {
    const [admin, penerbit, penerbit2, publik] = await ethers.getSigners();
    const Kontrak = await ethers.getContractFactory("SertifikatVerifikasi");
    const kontrak = await Kontrak.deploy();
    await kontrak.waitForDeployment();
    const root = ethers.keccak256(ethers.toUtf8Bytes("merkle-root-uji"));
    const publicId = ethers.encodeBytes32String("ac4e0e222a5058757fe6b4df5b87c7e1".slice(0, 31));
    return { kontrak, admin, penerbit, penerbit2, publik, root, publicId };
  }

  describe("Deployment", function () {
    it("menetapkan pembuat kontrak sebagai admin", async function () {
      const { kontrak, admin } = await loadFixture(deployFixture);
      expect(await kontrak.admin()).to.equal(admin.address);
    });
  });

  describe("Manajemen penerbit (RBAC on-chain)", function () {
    it("admin dapat menambah penerbit dan memancarkan event", async function () {
      const { kontrak, penerbit } = await loadFixture(deployFixture);
      await expect(kontrak.tambahPenerbit(penerbit.address))
        .to.emit(kontrak, "PenerbitDitambahkan").withArgs(penerbit.address);
      expect(await kontrak.isPenerbitActive(penerbit.address)).to.equal(true);
    });

    it("non-admin tidak dapat menambah penerbit", async function () {
      const { kontrak, publik } = await loadFixture(deployFixture);
      await expect(kontrak.connect(publik).tambahPenerbit(publik.address))
        .to.be.revertedWith("Hanya admin");
    });

    it("admin dapat mencabut penerbit", async function () {
      const { kontrak, penerbit } = await loadFixture(deployFixture);
      await kontrak.tambahPenerbit(penerbit.address);
      await expect(kontrak.cabutPenerbit(penerbit.address))
        .to.emit(kontrak, "PenerbitDicabut").withArgs(penerbit.address);
      expect(await kontrak.isPenerbitActive(penerbit.address)).to.equal(false);
    });

    it("non-admin tidak dapat mencabut penerbit", async function () {
      const { kontrak, penerbit, publik } = await loadFixture(deployFixture);
      await kontrak.tambahPenerbit(penerbit.address);
      await expect(kontrak.connect(publik).cabutPenerbit(penerbit.address))
        .to.be.revertedWith("Hanya admin");
    });
  });

  describe("Penyimpanan Merkle Root", function () {
    it("penerbit aktif dapat menyimpan root dan membacanya kembali", async function () {
      const { kontrak, penerbit, root, publicId } = await loadFixture(deployFixture);
      await kontrak.tambahPenerbit(penerbit.address);
      await expect(kontrak.connect(penerbit).simpanRoot(1001n, root, publicId))
        .to.emit(kontrak, "RootDisimpan").withArgs(1001n, root);
      expect(await kontrak.getRoot(1001n)).to.equal(root);
      expect(await kontrak.getBatchIdByPublicId(publicId)).to.equal(1001n);
      expect(await kontrak.verifyCertificate(publicId, root)).to.equal(true);
    });

    it("wallet yang tidak terdaftar tidak dapat menyimpan root", async function () {
      const { kontrak, publik, root, publicId } = await loadFixture(deployFixture);
      await expect(kontrak.connect(publik).simpanRoot(1n, root, publicId))
        .to.be.revertedWith("Bukan penerbit aktif");
    });

    it("penerbit yang sudah dicabut tidak dapat menyimpan root", async function () {
      const { kontrak, penerbit, root, publicId } = await loadFixture(deployFixture);
      await kontrak.tambahPenerbit(penerbit.address);
      await kontrak.cabutPenerbit(penerbit.address);
      await expect(kontrak.connect(penerbit).simpanRoot(1n, root, publicId))
        .to.be.revertedWith("Bukan penerbit aktif");
    });

    it("batch yang belum terdaftar mengembalikan root kosong", async function () {
      const { kontrak } = await loadFixture(deployFixture);
      expect(await kontrak.getRoot(999n)).to.equal(ethers.ZeroHash);
    });

    it("verifyCertificate menolak root yang tidak cocok", async function () {
      const { kontrak, penerbit, root, publicId } = await loadFixture(deployFixture);
      await kontrak.tambahPenerbit(penerbit.address);
      await kontrak.connect(penerbit).simpanRoot(7n, root, publicId);
      const rootLain = ethers.keccak256(ethers.toUtf8Bytes("root-lain"));
      await expect(kontrak.verifyCertificate(publicId, rootLain)).to.be.revertedWith("Merkle Root tidak cocok");
    });
  });

  describe("Biaya gas", function () {
    it("mencatat gas used untuk setiap fungsi", async function () {
      const { kontrak, penerbit, root, publicId } = await loadFixture(deployFixture);
      const g = async (txp) => (await (await txp).wait()).gasUsed;
      const tambah = await g(kontrak.tambahPenerbit(penerbit.address));
      const simpan = await g(kontrak.connect(penerbit).simpanRoot(42n, root, publicId));
      const cabut = await g(kontrak.cabutPenerbit(penerbit.address));
      console.log(`      gas tambahPenerbit=${tambah}, simpanRoot=${simpan}, cabutPenerbit=${cabut}`);
      expect(simpan).to.be.lessThan(100000n);
    });
  });
});
