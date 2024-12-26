# In

## confirmation-response
- offer_id: str
- confirmed: bool

## bid
- offer_id: str
- amount: int

## register-rental
- min_price: int
- max_price: int
- location: [float, float]

## rental-offer
- starting_price: int
- location: [float, float]

# Out

## auction_start
- offer_id: str
- starting_price: int
- location: [float, float]
- end_time: str
- current_highest_bid: int

## outbid_notification
- offer_id: str
- current_highest_bid: int

## auction_end
- offer_id: str

## confirmation_request
- offer_id: str
- bid_amount: int

## auction_result
- offer_id: str
- won: bool
