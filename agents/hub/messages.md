# In

## confirmation-response
- offer_id: str
- confirmed: bool

<!-- DONE -->
## bid
- offer_id: str
- amount: int

<!-- DONE -->
## register-rental
- min_price: int
- max_price: int
- location: [float, float]

<!-- DONE -->
## rental-offer
- starting_price: int
- location: [float, float]

# Out

<!-- DONE -->
## auction-start
- offer_id: str
- starting_price: int
- location: [float, float]
- end_time: str
- current_highest_bid: int

<!-- DONE -->
## outbid-notification
- offer_id: str
- current_highest_bid: int

<!-- DONE -->
## auction-stop
- offer_id: str

<!-- DONE -->
## confirmation-request
- offer_id: str
- bid_amount: int

<!-- DONE -->
## auction-lost
- offer_id: str

<!-- DONE -->
## auction-completed
- offer_id: str
- final_price: int
