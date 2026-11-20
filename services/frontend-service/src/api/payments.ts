import { request } from "./http";
import { normalizeWallet, type Role, type Wallet } from "./types";

export const paymentsApi = {
  async wallet(role: Role): Promise<Wallet> {
    const kind = role === "seller" ? "seller" : "buyer";
    return normalizeWallet(await request("payment", `/api/v1/wallets/${kind}`));
  },
};
