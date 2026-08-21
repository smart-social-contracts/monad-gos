import Text "mo:core/Text";
import Nat "mo:core/Nat";

module {
  public type Personality = {
    voice : Text;
    stance : Text;
    principles : [Text];
    description : Text;
  };

  public type Token = {
    mode : Text;
    token_id : Text;
    symbol : Text;
    canister_id : Text;
  };

  public type Draft = {
    step : Text;
    personality : Personality;
    token : Token;
    logo_data_url : Text;
  };

  public type State = {
    entered : Bool;
    completed : Bool;
    is_caller_authorized : Bool;
    creator : Text;
    registry_canister_id : Text;
    environment : Text;
    completed_at : Nat64;
    draft : Draft;
    personality : Personality;
    token : Token;
    logo_data_url : Text;
  };

  let VOICES : [Text] = ["austere", "warm", "playful"];
  let STANCES : [Text] = ["preserve", "balance", "experiment"];
  let PRINCIPLES : [Text] = [
    "treasury_honesty",
    "exit_is_voice",
    "propose_never_write",
    "short_replies",
    "cite_codex",
    "no_private_deals",
    "maximize_alignment",
    "plain_language",
  ];
  let STEPS : [Text] = ["welcome", "personality", "token", "branding", "launch"];
  let TOKEN_MODES : [Text] = ["none", "shared", "custom"];

  let DESCRIPTION_MAX : Nat = 2000;
  let LOGO_MAX : Nat = 1_572_864;

  public func emptyPersonality() : Personality {
    { voice = ""; stance = ""; principles = []; description = "" };
  };

  public func emptyToken() : Token {
    { mode = ""; token_id = ""; symbol = ""; canister_id = "" };
  };

  public func emptyDraft() : Draft {
    {
      step = "welcome";
      personality = emptyPersonality();
      token = emptyToken();
      logo_data_url = "";
    };
  };

  func inList(value : Text, allowed : [Text]) : Bool {
    for (item in allowed.vals()) {
      if (value == item) {
        return true;
      };
    };
    false;
  };

  func validateStep(step : Text) : ?Text {
    if (Text.size(step) == 0 or inList(step, STEPS)) {
      null;
    } else {
      ?"invalid setup step";
    };
  };

  func validatePrinciples(principles : [Text]) : ?Text {
    for (principle in principles.vals()) {
      if (not inList(principle, PRINCIPLES)) {
        return ?("invalid principle: " # principle);
      };
    };
    null;
  };

  func validateDescription(description : Text) : ?Text {
    if (Text.size(description) > DESCRIPTION_MAX) {
      ?("description exceeds maximum length (" # Nat.toText(DESCRIPTION_MAX) # " chars)");
    } else {
      null;
    };
  };

  func validateLogo(logo : Text) : ?Text {
    if (Text.size(logo) == 0) {
      return null;
    };
    if (Text.size(logo) > LOGO_MAX) {
      return ?("logo_data_url exceeds maximum size");
    };
    if (not Text.startsWith(logo, #text "data:image/")) {
      return ?("logo_data_url must start with data:image/");
    };
    null;
  };

  func validateVoice(voice : Text, required : Bool) : ?Text {
    if (Text.size(voice) == 0) {
      if (required) { ?"voice is required" } else { null };
    } else if (inList(voice, VOICES)) {
      null;
    } else {
      ?"invalid voice";
    };
  };

  func validateStance(stance : Text, required : Bool) : ?Text {
    if (Text.size(stance) == 0) {
      if (required) { ?"stance is required" } else { null };
    } else if (inList(stance, STANCES)) {
      null;
    } else {
      ?"invalid stance";
    };
  };

  func validateTokenMode(mode : Text, required : Bool) : ?Text {
    if (Text.size(mode) == 0) {
      if (required) { ?"token mode is required" } else { null };
    } else if (inList(mode, TOKEN_MODES)) {
      null;
    } else {
      ?"invalid token mode";
    };
  };

  func validateTokenDraft(token : Token) : ?Text {
    switch (validateTokenMode(token.mode, false)) {
      case (?err) ?err;
      case null {
        switch (token.mode) {
          case ("custom") {
            if (Text.size(token.canister_id) == 0) {
              ?"custom token requires canister_id";
            } else {
              null;
            };
          };
          case ("shared") {
            if (Text.size(token.token_id) == 0 or Text.size(token.canister_id) == 0) {
              ?"shared token requires token_id and canister_id";
            } else {
              null;
            };
          };
          case _ null;
        };
      };
    };
  };

  func validateTokenLaunch(token : Token) : ?Text {
    switch (validateTokenMode(token.mode, true)) {
      case (?err) ?err;
      case null {
        switch (token.mode) {
          case ("none") null;
          case ("custom") {
            if (Text.size(token.canister_id) == 0) {
              ?"custom token requires canister_id";
            } else {
              null;
            };
          };
          case ("shared") {
            if (Text.size(token.token_id) == 0 or Text.size(token.canister_id) == 0) {
              ?"shared token requires token_id and canister_id";
            } else {
              null;
            };
          };
          case _ ?"invalid token mode";
        };
      };
    };
  };

  public func mergePersonality(existing : Personality, incoming : Personality) : Personality {
    {
      voice = if (Text.size(incoming.voice) > 0) incoming.voice else existing.voice;
      stance = if (Text.size(incoming.stance) > 0) incoming.stance else existing.stance;
      principles = if (incoming.principles.size() > 0) incoming.principles else existing.principles;
      description = if (Text.size(incoming.description) > 0) incoming.description else existing.description;
    };
  };

  public func mergeToken(existing : Token, incoming : Token) : Token {
    {
      mode = if (Text.size(incoming.mode) > 0) incoming.mode else existing.mode;
      token_id = if (Text.size(incoming.token_id) > 0) incoming.token_id else existing.token_id;
      symbol = if (Text.size(incoming.symbol) > 0) incoming.symbol else existing.symbol;
      canister_id = if (Text.size(incoming.canister_id) > 0) incoming.canister_id else existing.canister_id;
    };
  };

  public func mergeDraft(existing : Draft, incoming : Draft) : Draft {
    {
      step = if (Text.size(incoming.step) > 0) incoming.step else existing.step;
      personality = mergePersonality(existing.personality, incoming.personality);
      token = mergeToken(existing.token, incoming.token);
      logo_data_url = if (Text.size(incoming.logo_data_url) > 0) {
        incoming.logo_data_url;
      } else {
        existing.logo_data_url;
      };
    };
  };

  public func validateDraft(draft : Draft) : ?Text {
    switch (validateStep(draft.step)) {
      case (?err) ?err;
      case null {
        switch (validateVoice(draft.personality.voice, false)) {
          case (?err) ?err;
          case null {
            switch (validateStance(draft.personality.stance, false)) {
              case (?err) ?err;
              case null {
                switch (validatePrinciples(draft.personality.principles)) {
                  case (?err) ?err;
                  case null {
                    switch (validateDescription(draft.personality.description)) {
                      case (?err) ?err;
                      case null {
                        switch (validateTokenDraft(draft.token)) {
                          case (?err) ?err;
                          case null validateLogo(draft.logo_data_url);
                        };
                      };
                    };
                  };
                };
              };
            };
          };
        };
      };
    };
  };

  public func validateForLaunch(draft : Draft) : ?Text {
    switch (validateStep(draft.step)) {
      case (?err) ?err;
      case null {
        switch (validateVoice(draft.personality.voice, true)) {
          case (?err) ?err;
          case null {
            switch (validateStance(draft.personality.stance, true)) {
              case (?err) ?err;
              case null {
                switch (validatePrinciples(draft.personality.principles)) {
                  case (?err) ?err;
                  case null {
                    switch (validateDescription(draft.personality.description)) {
                      case (?err) ?err;
                      case null {
                        switch (draft.token.mode) {
                          case ("") validateLogo(draft.logo_data_url);
                          case ("none") validateLogo(draft.logo_data_url);
                          case (_) {
                            switch (validateTokenLaunch(draft.token)) {
                              case (?err) ?err;
                              case null validateLogo(draft.logo_data_url);
                            };
                          };
                        };
                      };
                    };
                  };
                };
              };
            };
          };
        };
      };
    };
  };
};
