
deu = 10


def number2bin(num, perimtedLength = 8):
        binary = bin(num).replace('0b', '')
        if len(binary) > perimtedLength:
            raise ValueError(f'Expected max length {perimtedLength}, got number {num} -> len {len(num)}')
        return '0' * (perimtedLength  - len(binary)) + binary

print([i for i in number2bin(254)])





