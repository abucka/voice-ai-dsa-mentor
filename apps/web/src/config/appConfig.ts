import { environment as development } from "../environment.development";
import { environment as production } from "../environment.production";

const environment = import.meta.env.PROD ? production : development;

export const REQUIRE_SIGNIN_PARAM = environment.requireSignIn;
