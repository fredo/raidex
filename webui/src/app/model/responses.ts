import { Offer } from './offer';

export interface ApiResponse<T> {
    readonly data: T;
}

export interface OffersData {
    readonly buys: Offer[];
    readonly sells: Offer[];
}

export interface OrderResponse {
    readonly type: string;
    readonly amount: string;
    readonly price: string;
    readonly order_id: number;
    readonly filledAmount: string;
    readonly open: Boolean;
    readonly canceled: Boolean;
}

export interface ChannelResponse {
    readonly partner_address: string;
    readonly token_address: string;
    readonly total_deposit: number;
}
