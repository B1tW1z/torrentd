"""
Piece selection: rarest-first with endgame mode when few pieces remain.
"""
from .piece import Piece, BLOCK_SIZE


class PieceManager:
    def __init__(self, torrent, download_path="download.bin"):
        self.torrent = torrent
        self.download_path = download_path
        self.num_pieces = torrent.num_pieces
        self.piece_length = torrent.piece_length
        self.total_length = torrent.length

        self.pieces = []
        for i in range(self.num_pieces):
            size = self.piece_length
            if i == self.num_pieces - 1:
                size = self.total_length % self.piece_length or self.piece_length
            hash_bytes = torrent.pieces[i * 20:(i + 1) * 20]
            self.pieces.append(Piece(i, size, hash_bytes))

        self.completed = set()
        self.in_progress = set()
        self.availability = {i: 0 for i in range(self.num_pieces)}

    def update_availability(self, bitfield):
        """Update per-piece availability from peer BITFIELD. bitfield is bytes or list of bools."""
        if isinstance(bitfield, bytes):
            for i in range(min(len(bitfield) * 8, self.num_pieces)):
                if bitfield[i // 8] & (0x80 >> (i % 8)):
                    self.availability[i] = self.availability.get(i, 0) + 1
        else:
            for i, has_piece in enumerate(bitfield):
                if i >= self.num_pieces:
                    break
                if has_piece:
                    self.availability[i] = self.availability.get(i, 0) + 1

    def next_piece(self):
        """Rarest-first: pick a piece not completed and not in progress, with lowest availability."""
        candidates = [
            p for p in self.pieces
            if p.index not in self.completed and p.index not in self.in_progress
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda p: self.availability.get(p.index, 0))
        piece = candidates[0]
        self.in_progress.add(piece.index)
        return piece

    def endgame(self):
        """True when remaining pieces < threshold (e.g. 5) — allow duplicate block requests."""
        remaining = self.num_pieces - len(self.completed)
        return remaining < 5

    def mark_completed(self, piece_index):
        self.completed.add(piece_index)
        self.in_progress.discard(piece_index)

    def mark_in_progress_free(self, piece_index):
        self.in_progress.discard(piece_index)

    def is_done(self):
        return len(self.completed) == self.num_pieces
