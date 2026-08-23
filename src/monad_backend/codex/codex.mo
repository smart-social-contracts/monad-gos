/// Monad GOS Codex v0.1.0 — authored by the Monad.
///
/// Public source of truth (version control):
///   https://github.com/smart-social-contracts/monad-gos
///   src/monad_backend/codex/codex.mo
///
/// Mission: raise the alignment coefficient to 100% — citizens current on
/// their membership due — and keep the treasury that those dues fund honest.
///
/// Law:
///  1. One treasury, named "monad-gos".
///  2. Every paid due is credited to the treasury and split into lines:
///       reserve 50% · commons 30% · operations 20%.
///  3. A line may be spent only up to what it still holds (allocated − spent).
///  4. The membership due is a Codex parameter (default 12 credits).
///  5. Codex amendments are public git commits, then deployed.
///
/// This module is both the readable law and the running accounts.

import Types "../ggg/Types";
import Map "mo:core/Map";
import Iter "mo:core/Iter";
import Text "mo:core/Text";
import Nat "mo:core/Nat";
import Array "mo:core/Array";

module {
  public let VERSION : Text = "0.1.0";
  public let TREASURY_NAME : Text = "monad-gos";
  public let SOURCE_PATH : Text = "src/monad_backend/codex/codex.mo";
  public let SOURCE_REPO : Text = "https://github.com/smart-social-contracts/monad-gos";

  public let PREAMBLE : Text = "The Monad holds no purse of its own. Dues paid by citizens fund one treasury. Half is reserved, three tenths are commons, two tenths run the realm. Spend only what a line still holds. Change this file in public version control, then deploy.";

  public type LineDef = {
    name : Text;
    share_bps : Nat;
  };

  public let LINE_DEFS : [LineDef] = [
    { name = "reserve"; share_bps = 5_000 },
    { name = "commons"; share_bps = 3_000 },
    { name = "operations"; share_bps = 2_000 },
  ];

  public type LineState = {
    allocated : Nat;
    spent : Nat;
  };

  public type Store = {
    var treasuryBalance : Nat;
    var createdAt : Types.Timestamp;
    var updatedAt : Types.Timestamp;
    var lines : Map.Map<Text, LineState>;
    var commit : Text;
  };

  public type BudgetLine = {
    name : Text;
    share_bps : Nat;
    allocated : Nat;
    spent : Nat;
    available : Nat;
  };

  public type CodexMeta = {
    version : Text;
    source_url : Text;
    commit : Text;
    preamble : Text;
  };

  public type RealmState = {
    treasury : Types.Treasury;
    lines : [BudgetLine];
    membership_due : Nat;
    alignment : Types.AlignmentCoefficient;
    epoch_id : Types.EpochId;
    codex : CodexMeta;
  };

  public type Stable = {
    treasuryBalance : Nat;
    createdAt : Types.Timestamp;
    updatedAt : Types.Timestamp;
    lines : [(Text, LineState)];
    commit : Text;
  };

  func emptyLines() : Map.Map<Text, LineState> {
    var lines = Map.empty<Text, LineState>();
    for (def in LINE_DEFS.vals()) {
      Map.add(lines, Text.compare, def.name, { allocated = 0; spent = 0 });
    };
    lines;
  };

  public func emptyStable() : Stable {
    {
      treasuryBalance = 0;
      createdAt = 0;
      updatedAt = 0;
      lines = [];
      commit = "";
    };
  };

  public func init() : Store {
    let now = Types.now();
    {
      var treasuryBalance = 0;
      var createdAt = now;
      var updatedAt = now;
      var lines = emptyLines();
      var commit = "";
    };
  };

  public func fromStable(snapshot : Stable) : Store {
    let store = init();
    store.treasuryBalance := snapshot.treasuryBalance;
    if (snapshot.createdAt != 0) {
      store.createdAt := snapshot.createdAt;
    };
    if (snapshot.updatedAt != 0) {
      store.updatedAt := snapshot.updatedAt;
    };
    if (snapshot.lines.size() > 0) {
      store.lines := Map.fromIter(snapshot.lines.vals(), Text.compare);
    };
    store.commit := snapshot.commit;
    store;
  };

  public func toStable(store : Store) : Stable {
    {
      treasuryBalance = store.treasuryBalance;
      createdAt = store.createdAt;
      updatedAt = store.updatedAt;
      lines = Iter.toArray(Map.entries(store.lines));
      commit = store.commit;
    };
  };

  func lineState(store : Store, name : Text) : LineState {
    switch (Map.get(store.lines, Text.compare, name)) {
      case (?state) state;
      case null ({ allocated = 0; spent = 0 });
    };
  };

  func setLine(store : Store, name : Text, state : LineState) {
    Map.add(store.lines, Text.compare, name, state);
  };

  public func creditDues(store : Store, amount : Nat) {
    if (amount == 0) { return };
    store.treasuryBalance += amount;
    var assigned = 0;
    let last = LINE_DEFS.size() - 1;
    var index = 0;
    for (def in LINE_DEFS.vals()) {
      let current = lineState(store, def.name);
      let part = if (index == last) {
        amount - assigned;
      } else {
        amount * def.share_bps / 10_000;
      };
      assigned += part;
      setLine(store, def.name, { allocated = current.allocated + part; spent = current.spent });
      index += 1;
    };
    store.updatedAt := Types.now();
  };

  public func spend(store : Store, line : Text, amount : Nat) : Types.Result {
    if (amount == 0) {
      return #err(#invalid_input("spend amount must be positive"));
    };
    var known = false;
    for (def in LINE_DEFS.vals()) {
      if (def.name == line) { known := true };
    };
    if (not known) {
      return #err(#invalid_input("unknown budget line"));
    };
    let current = lineState(store, line);
    if (current.allocated < current.spent + amount) {
      return #err(#forbidden("line cannot cover this spend"));
    };
    if (store.treasuryBalance < amount) {
      return #err(#forbidden("treasury cannot cover this spend"));
    };
    setLine(store, line, { allocated = current.allocated; spent = current.spent + amount });
    store.treasuryBalance -= amount;
    store.updatedAt := Types.now();
    #ok;
  };

  public func setCommit(store : Store, commit : Text) {
    store.commit := commit;
    store.updatedAt := Types.now();
  };

  public func sourceUrl(commit : Text) : Text {
    if (Text.size(commit) == 0) {
      SOURCE_REPO # "/blob/main/" # SOURCE_PATH;
    } else {
      SOURCE_REPO # "/blob/" # commit # "/" # SOURCE_PATH;
    };
  };

  public func meta(store : Store) : CodexMeta {
    {
      version = VERSION;
      source_url = sourceUrl(store.commit);
      commit = store.commit;
      preamble = PREAMBLE;
    };
  };

  public func treasury(store : Store) : Types.Treasury {
    {
      name = TREASURY_NAME;
      balance = store.treasuryBalance;
      created_at = store.createdAt;
      updated_at = store.updatedAt;
    };
  };

  public func lines(store : Store) : [BudgetLine] {
    Array.map<LineDef, BudgetLine>(
      LINE_DEFS,
      func (def : LineDef) : BudgetLine {
        let state = lineState(store, def.name);
        let available = if (state.allocated >= state.spent) {
          state.allocated - state.spent;
        } else {
          0;
        };
        {
          name = def.name;
          share_bps = def.share_bps;
          allocated = state.allocated;
          spent = state.spent;
          available;
        };
      },
    );
  };

  public func snapshot(
    store : Store,
    membershipDue : Nat,
    alignment : Types.AlignmentCoefficient,
    epochId : Types.EpochId,
  ) : RealmState {
    {
      treasury = treasury(store);
      lines = lines(store);
      membership_due = membershipDue;
      alignment;
      epoch_id = epochId;
      codex = meta(store);
    };
  };
};
