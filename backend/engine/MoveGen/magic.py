import engine.MoveGen.Attack as Attack 
from engine.bitboard.utils import count_bits
import engine.bitboard.bitwise as bitwise
import random

def transform(b, magic, bits):
    return (bitwise.rshift((b * magic), (64 - bits))) & 0xFFF

def random_uint64():
    u1 = random.getrandbits(16)
    u2 = random.getrandbits(16)
    u3 = random.getrandbits(16)
    u4 = random.getrandbits(16)
    return u1 | (u2 << 16) | (u3 << 32) | (u4 << 48)

def random_uint64_fewbits():
    return random_uint64() & random_uint64() & random_uint64()

BitTable = [
    63, 30, 3, 32, 25, 41, 22, 33, 15, 50, 42, 13, 11, 53, 19, 34, 61, 29, 2,
    51, 21, 43, 45, 10, 18, 47, 1, 54, 9, 57, 0, 35, 62, 31, 40, 4, 49, 5, 52,
    26, 60, 6, 23, 44, 46, 27, 56, 16, 7, 39, 48, 24, 59, 14, 12, 55, 38, 28,
    58, 20, 37, 17, 36, 8
]

def pop_first_bit(bb):
    b = bb ^ (bb - 1)
    fold = ((b & 0xffffffff) ^ bitwise.rshift(b, 32)) & 0xffffffff
    bb &= (bb - 1)
    index = bitwise.rshift(((fold * 0x783a9b23) & 0xffffffff), 26)
    return BitTable[index], bb


def index_to_board(index, bits, m):
    result = 0 
    for i in range(bits):
        j, m = pop_first_bit(m)  
        if index & (1 << i): 
            result |= (1 << j) 
    return result

def magic(index, shift, bishop=False):
    mask = Attack.bishop_at(index) if bishop else Attack.rook_at(index)
    n = count_bits(mask)
    
    used = [0] * 4096
    blockers = [0] * 4096
    attacks = [0] * 4096

    for _ in range(0, 100000000):
        magic = random_uint64_fewbits()
        if count_bits((mask * magic) & 0xFF00000000000000) < 6:
            continue
        
        fail = False
        for i in range(0, bitwise.lshift(1, n)):
            blockers[i] = index_to_board(i, n, mask)
            attacks[i] = Attack.bishop_at_relative(index, blockers[i]) if bishop else Attack.rook_at_relative(index, blockers[i])
            j = transform(blockers[i], magic, shift)
            
            if j >= 4096: 
                continue
            
            if used[j] == 0:
                used[j] = attacks[i]
            elif used[j] != attacks[i]:
                fail = True
                break 

        if not fail:
            return magic

    print("** FAILED FINDING MAGIC **")
    return 0


ROOK_MAGICS = [
    0xa8002c000108020,0x6c00049b0002001,0x100200010090040,0x2480041000800801,
    0x280028004000800,0x900410008040022,0x280020001001080,0x2880002041000080,
    0xa000800080400034,0x4808020004000,0x2290802004801000,0x411000d00100020,
    0x402800800040080,0xb000401004208,0x2409000100040200,0x1002100004082,
    0x22878001e24000,0x1090810021004010,0x801030040200012,0x500808008001000,
    0xa08018014000880,0x8000808004000200,0x201008080010200,0x801020000441091,
    0x800080204005,0x1040200040100048,0x120200402082,0xd14880480100080,
    0x12040280080080,0x100040080020080,0x9020010080800200,0x813241200148449,
    0x491604001800080,0x100401000402001,0x4820010021001040,0x400402202000812,
    0x209009005000802,0x810800601800400,0x4301083214000150,0x204026458e001401,
    0x40204000808000,0x8001008040010020,0x8410820820420010,0x1003001000090020,
    0x804040008008080,0x12000810020004,0x1000100200040208,0x430000a044020001,
    0x280009023410300,0xe0100040002240,0x200100401700,0x2244100408008080,
    0x8000400801980,0x2000810040200,0x8010100228810400,0x2000009044210200,
    0x4080008040102101,0x40002080411d01,0x2005524060000901,0x502001008400422,
    0x489a000810200402,0x1004400080a13,0x4000011008020084,0x26002114058042
]

BISHOP_MAGICS = [
    0x89a1121896040240,0x2004844802002010,0x2068080051921000,0x62880a0220200808,
    0x4042004000000,0x100822020200011,0xc00444222012000a,0x28808801216001,
    0x400492088408100,0x201c401040c0084,0x840800910a0010,0x82080240060,
    0x2000840504006000,0x30010c4108405004,0x1008005410080802,0x8144042209100900,
    0x208081020014400,0x4800201208ca00,0xf18140408012008,0x1004002802102001,
    0x841000820080811,0x40200200a42008,0x800054042000,0x88010400410c9000,
    0x520040470104290,0x1004040051500081,0x2002081833080021,0x400c00c010142,
    0x941408200c002000,0x658810000806011,0x188071040440a00,0x4800404002011c00,
    0x104442040404200,0x511080202091021,0x4022401120400,0x80c0040400080120,
    0x8040010040820802,0x480810700020090,0x102008e00040242,0x809005202050100,
    0x8002024220104080,0x431008804142000,0x19001802081400,0x200014208040080,
    0x3308082008200100,0x41010500040c020,0x4012020c04210308,0x208220a202004080,
    0x111040120082000,0x6803040141280a00,0x2101004202410000,0x8200000041108022,
    0x21082088000,0x2410204010040,0x40100400809000,0x822088220820214,
    0x40808090012004,0x910224040218c9,0x402814422015008,0x90014004842410,
    0x1000042304105,0x10008830412a00,0x2520081090008908,0x40102000a0a60140
]


    