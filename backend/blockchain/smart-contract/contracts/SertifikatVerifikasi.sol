// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract SertifikatVerifikasi {
    address public admin;
    
    mapping(address => bool) public penerbitAktif;
    mapping(uint256 => bytes32) public merkleRoots;
    
    // simpan public id di blockchain
    mapping(bytes32 => uint256) public publicIdToBatchId;

    event PenerbitDitambahkan(address indexed wallet);
    event PenerbitDicabut(address indexed wallet);
    event RootDisimpan(uint256 indexed batchId, bytes32 merkleRoot);
    event PublicIdTerdaftar(bytes32 indexed publicId, uint256 batchId);

    modifier hanyaAdmin() {
        require(msg.sender == admin, "Hanya admin");
        _;
    }

    modifier hanyaPenerbitAktif() {
        require(penerbitAktif[msg.sender], "Bukan penerbit aktif");
        _;
    }

    constructor() {
        admin = msg.sender;
    }

    // fungsi simpan root dan publik id
    function simpanRoot(
        uint256 _batchId, 
        bytes32 _merkleRoot,
        bytes32 _publicId
    ) external hanyaPenerbitAktif {
        merkleRoots[_batchId] = _merkleRoot;
        publicIdToBatchId[_publicId] = _batchId;
        emit RootDisimpan(_batchId, _merkleRoot);
        emit PublicIdTerdaftar(_publicId, _batchId);
    }

    // verify only desentralisasi
    function verifyCertificate(
        bytes32 _publicId,
        bytes32 _merkleRoot
    ) external view returns (bool) {
        uint256 batchId = publicIdToBatchId[_publicId];
        require(batchId > 0, "Public ID tidak terdaftar");
        require(merkleRoots[batchId] == _merkleRoot, "Merkle Root tidak cocok");
        return true;
    }

    //cek publik id
    function getBatchIdByPublicId(bytes32 _publicId) external view returns (uint256) {
        return publicIdToBatchId[_publicId];
    }

    //tambah penerbit
    function tambahPenerbit(address _wallet) external hanyaAdmin {
        penerbitAktif[_wallet] = true;
        emit PenerbitDitambahkan(_wallet);
    }

    function cabutPenerbit(address _wallet) external hanyaAdmin {
        penerbitAktif[_wallet] = false;
        emit PenerbitDicabut(_wallet);
    }

    function isPenerbitActive(address _wallet) external view returns (bool) {
        return penerbitAktif[_wallet];
    }

    function getRoot(uint256 _batchId) external view returns (bytes32) {
        return merkleRoots[_batchId];
    }
}