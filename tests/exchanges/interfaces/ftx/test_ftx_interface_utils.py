from typing import List

def get_open_order_ids(open_orders: List[dict]) -> List[int]:

    ids: List[int] = []

    for order in open_orders:
        ids.append(int(order["id"]))
    
    return ids