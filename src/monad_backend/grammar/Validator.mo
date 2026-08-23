import Types "../ggg/Types";
import Text "mo:core/Text";
import Nat "mo:core/Nat";
import Array "mo:core/Array";
import Iter "mo:core/Iter";
import Char "mo:core/Char";
import Nat32 "mo:core/Nat32";

module {
  public type Config = {
    spend_cap : Nat;
    forbidden_operations : [Text];
  };

  public type ProposalPayload = {
    title : Text;
    description : Text;
    spend : Nat;
    operations : [Text];
  };

  public func defaultConfig() : Config {
    {
      spend_cap = 1_000_000;
      forbidden_operations = ["mint_unbounded", "seize_all", "revoke_all_mandates"];
    };
  };

  public func payloadFromInput(input : Types.SubmitProposalInput) : ProposalPayload {
    {
      title = input.title;
      description = input.description;
      spend = parseSpend(input.metadata);
      operations = parseOperations(input.metadata);
    };
  };

  public func validate(config : Config, proposal : ProposalPayload) : Types.Result {
    if (Text.size(proposal.title) == 0) {
      return #err(#invalid_input("title is required"));
    };
    if (Text.size(proposal.description) == 0) {
      return #err(#invalid_input("description is required"));
    };
    if (proposal.spend > config.spend_cap) {
      return #err(#forbidden("spend exceeds cap"));
    };
    for (operation in proposal.operations.vals()) {
      for (forbidden in config.forbidden_operations.vals()) {
        if (operation == forbidden) {
          return #err(#forbidden("forbidden operation: " # operation));
        };
      };
    };
    #ok;
  };

  public func validateInput(config : Config, input : Types.SubmitProposalInput) : Types.Result {
    validate(config, payloadFromInput(input));
  };

  func parseSpend(metadata : Text) : Nat {
    let lines = Text.split(metadata, #char '\n');
    for (line in lines) {
      if (Text.startsWith(line, #text "spend:")) {
        switch (parseNatPrefix(Text.trim(line, #text "spend:"))) {
          case (?value) return value;
          case null {};
        };
      };
    };
    0;
  };

  func parseOperations(metadata : Text) : [Text] {
    let lines = Text.split(metadata, #char '\n');
    Array.filterMap<Text, Text>(
      Iter.toArray(lines),
      func (line : Text) : ?Text {
        if (Text.startsWith(line, #text "op:")) {
          ?Text.trim(line, #text "op:");
        } else {
          null;
        };
      },
    );
  };

  func parseNatPrefix(text : Text) : ?Nat {
    var value = 0;
    var found = false;
    label digits for (char in text.chars()) {
      if (char >= '0' and char <= '9') {
        found := true;
        value := value * 10 + Nat32.toNat(Char.toNat32(char) - Char.toNat32('0'));
      } else if (found) {
        break digits;
      };
    };
    if (found) { ?value } else { null };
  };
};
