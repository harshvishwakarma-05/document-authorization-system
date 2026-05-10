// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DocumentRegistry {
    struct DocumentRecord {
        address issuer;
        string title;
        string fileName;
        uint256 timestamp;
        bool exists;
    }

    mapping(bytes32 => DocumentRecord) private records;

    event DocumentRegistered(
        bytes32 indexed documentHash,
        address indexed issuer,
        string title,
        string fileName,
        uint256 timestamp
    );

    function registerDocument(bytes32 documentHash, string calldata title, string calldata fileName) external {
        require(documentHash != bytes32(0), "Invalid document hash");
        require(!records[documentHash].exists, "Document already registered");

        records[documentHash] = DocumentRecord({
            issuer: msg.sender,
            title: title,
            fileName: fileName,
            timestamp: block.timestamp,
            exists: true
        });

        emit DocumentRegistered(documentHash, msg.sender, title, fileName, block.timestamp);
    }

    function verifyDocument(bytes32 documentHash)
        external
        view
        returns (bool exists, address issuer, string memory title, string memory fileName, uint256 timestamp)
    {
        DocumentRecord memory record = records[documentHash];
        return (record.exists, record.issuer, record.title, record.fileName, record.timestamp);
    }
}