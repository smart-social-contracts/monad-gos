import Types "../ggg/Types";
import Map "mo:core/Map";
import Iter "mo:core/Iter";
import Text "mo:core/Text";
import Array "mo:core/Array";
import Result "mo:core/Result";
import Principal "mo:core/Principal";
import Nat "mo:core/Nat";

module {
  public type Store = {
    var currentEpoch : Nat;
    var nextWishId : Nat;
    var wishes : Map.Map<Types.WishId, Types.Wish>;
    var wishesByEpoch : Map.Map<Types.EpochId, [Types.WishId]>;
    var sealedEpochs : Map.Map<Types.EpochId, Bool>;
  };

  public func init() : Store {
    {
      var currentEpoch = 0;
      var nextWishId = 1;
      var wishes = Map.empty<Types.WishId, Types.Wish>();
      var wishesByEpoch = Map.empty<Types.EpochId, [Types.WishId]>();
      var sealedEpochs = Map.empty<Types.EpochId, Bool>();
    };
  };

  public func currentEpochId(store : Store) : Types.EpochId {
    Types.epochId(store.currentEpoch);
  };

  public func isEpochSealed(store : Store, epoch : Types.EpochId) : Bool {
    switch (Map.get(store.sealedEpochs, Text.compare, epoch)) {
      case (?true) true;
      case _ false;
    };
  };

  public func submit(
    store : Store,
    author : Principal,
    input : Types.SubmitWishInput,
  ) : Types.Result_WishId {
    if (input.ciphertext.size() == 0) {
      return #err(#invalid_input("ciphertext is required"));
    };
    switch (Types.validateDomain(input.domain)) {
      case (?err) return #err(err);
      case null {};
    };
    if (input.epoch != currentEpochId(store)) {
      return #err(#invalid_input("wish epoch must match current open epoch"));
    };
    if (isEpochSealed(store, input.epoch)) {
      return #err(#forbidden("epoch is sealed"));
    };

    let id = Types.entityId("wish", store.nextWishId);
    store.nextWishId += 1;
    let wish : Types.Wish = {
      id;
      author = Types.principalId(author);
      domain = input.domain;
      ciphertext = input.ciphertext;
      epoch = input.epoch;
      assistant_id = input.assistant_id;
      created_at = Types.now();
    };

    Map.add(store.wishes, Text.compare, id, wish);
    let existing = switch (Map.get(store.wishesByEpoch, Text.compare, input.epoch)) {
      case (?ids) ids;
      case null [];
    };
    Map.add(store.wishesByEpoch, Text.compare, input.epoch, Array.concat(existing, [id]));
    #ok(id);
  };

  public func get(store : Store, id : Types.WishId) : ?Types.Wish {
    Map.get(store.wishes, Text.compare, id);
  };

  public func listByEpoch(store : Store, epoch : Types.EpochId) : [Types.Wish] {
    switch (Map.get(store.wishesByEpoch, Text.compare, epoch)) {
      case (?ids) {
        Array.filterMap<Types.WishId, Types.Wish>(
          ids,
          func (id : Types.WishId) : ?Types.Wish {
            Map.get(store.wishes, Text.compare, id);
          },
        );
      };
      case null [];
    };
  };

  public func seal(store : Store) : Result.Result<Types.EpochId, Types.GggError> {
    let epoch = currentEpochId(store);
    if (isEpochSealed(store, epoch)) {
      return #err(#conflict("current epoch is already sealed"));
    };
    Map.add(store.sealedEpochs, Text.compare, epoch, true);
    store.currentEpoch += 1;
    #ok(epoch);
  };

  public type Stable = {
    currentEpoch : Nat;
    nextWishId : Nat;
    wishes : [(Types.WishId, Types.Wish)];
    wishesByEpoch : [(Types.EpochId, [Types.WishId])];
    sealedEpochs : [Types.EpochId];
  };

  public func toStable(store : Store) : Stable {
    {
      currentEpoch = store.currentEpoch;
      nextWishId = store.nextWishId;
      wishes = Iter.toArray(Map.entries(store.wishes));
      wishesByEpoch = Iter.toArray(Map.entries(store.wishesByEpoch));
      sealedEpochs = Iter.toArray(Map.keys(store.sealedEpochs));
    };
  };

  public func fromStable(snapshot : Stable) : Store {
    let store = init();
    store.currentEpoch := snapshot.currentEpoch;
    store.nextWishId := snapshot.nextWishId;
    store.wishes := Map.fromIter(snapshot.wishes.vals(), Text.compare);
    store.wishesByEpoch := Map.fromIter(snapshot.wishesByEpoch.vals(), Text.compare);
    for (epoch in snapshot.sealedEpochs.vals()) {
      Map.add(store.sealedEpochs, Text.compare, epoch, true);
    };
    store;
  };
};
