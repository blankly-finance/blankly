from typing import List


def get_open_order_ids(open_orders: List[dict]) -> List[str]:

    ids: List[str] = []

    for order in open_orders:
        ids.append(str(order["id"]))
    
    return ids
