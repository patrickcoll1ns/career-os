from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentChunk:
    index: int
    text: str


class DocumentChunker:
    """Split extracted text into bounded, overlapping, word-aware chunks."""

    def __init__(self, max_characters: int = 1200, overlap_characters: int = 200):
        if max_characters < 1:
            raise ValueError("max_characters must be positive.")
        if overlap_characters < 0 or overlap_characters >= max_characters:
            raise ValueError(
                "overlap_characters must be non-negative and smaller than the chunk."
            )
        self.max_characters = max_characters
        self.overlap_characters = overlap_characters

    def split(self, text: str) -> list[DocumentChunk]:
        words = self._bounded_words(text)
        if not words:
            return []

        chunks: list[DocumentChunk] = []
        start = 0

        while start < len(words):
            end = start
            character_count = 0

            while end < len(words):
                separator_size = 1 if end > start else 0
                proposed_size = character_count + separator_size + len(words[end])
                if proposed_size > self.max_characters:
                    break
                character_count = proposed_size
                end += 1

            chunks.append(
                DocumentChunk(
                    index=len(chunks),
                    text=" ".join(words[start:end]),
                )
            )

            if end == len(words):
                break
            start = self._overlap_start(words, start, end)

        return chunks

    def _bounded_words(self, text: str) -> list[str]:
        words: list[str] = []
        for word in text.split():
            words.extend(
                word[index : index + self.max_characters]
                for index in range(0, len(word), self.max_characters)
            )
        return words

    def _overlap_start(self, words: list[str], start: int, end: int) -> int:
        overlap_start = end
        overlap_size = 0

        while overlap_start > start + 1:
            word = words[overlap_start - 1]
            separator_size = 1 if overlap_size else 0
            proposed_size = overlap_size + separator_size + len(word)
            if proposed_size > self.overlap_characters:
                break
            overlap_start -= 1
            overlap_size = proposed_size

        return overlap_start
