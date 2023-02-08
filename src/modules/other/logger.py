class TraderLogger:

    OKGREEN = '\033[92m'
    OKRED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    def __init__(self) -> None:
        self.prefix = f'[{self.BOLD}{self.OKGREEN}Trader{self.ENDC}] '
        print(self.prefix + 'logger active.')

    def open_position(self, timestamp, price):
        print(self.prefix +
              f'opening position, timestamp is {timestamp}, price is {price}')

    def log(self, message):
        print(self.prefix + message)

    def pnl(self, pnl):
        color = self.OKGREEN if pnl > 0 else self.OKRED
        symbol = '+' if pnl > 0 else '-'
        print(f'{color}{symbol}{pnl}{self.ENDC}')