import Types "../ggg/Types";
import Map "mo:core/Map";
import Iter "mo:core/Iter";
import Nat "mo:core/Nat";
import Float "mo:core/Float";
import Principal "mo:core/Principal";
import Array "mo:core/Array";

module {
  public type Store = {
    var lastPaidEpoch : Map.Map<Principal, Nat>;
    var trendHistory : [Types.AlignmentTrendPoint];
    var membershipDue : Nat;
  };

  public func init(membershipDue : Nat) : Store {
    {
      var lastPaidEpoch = Map.empty<Principal, Nat>();
      var trendHistory = [];
      var membershipDue = membershipDue;
    };
  };

  public func recordDuePayment(store : Store, citizen : Principal, epoch : Nat) {
    Map.add(store.lastPaidEpoch, Principal.compare, citizen, epoch);
  };

  func computeCounts(store : Store, currentEpoch : Nat) : { total : Nat; current : Nat } {
    var total = 0;
    var current = 0;
    for ((_, paidEpoch) in Map.entries(store.lastPaidEpoch)) {
      total += 1;
      if (paidEpoch >= currentEpoch) {
        current += 1;
      };
    };
    { total; current };
  };

  func coefficientFraction(total : Nat, current : Nat) : Float {
    if (total == 0) {
      0.0;
    } else {
      Float.fromInt(current) / Float.fromInt(total);
    };
  };

  public func compute(store : Store, currentEpoch : Nat) : Types.AlignmentCoefficient {
    let counts = computeCounts(store, currentEpoch);
    {
      coefficient = coefficientFraction(counts.total, counts.current);
      citizens_total = counts.total;
      citizens_current = counts.current;
      membership_due = store.membershipDue;
      as_of = Types.now();
    };
  };

  public func trend(store : Store) : [Types.AlignmentTrendPoint] {
    store.trendHistory;
  };

  public func snapshotEpoch(store : Store, epoch : Nat) {
    let snapshot = compute(store, epoch);
    let point : Types.AlignmentTrendPoint = {
      epoch = Types.epochId(epoch);
      coefficient = snapshot.coefficient;
      as_of = snapshot.as_of;
    };
    store.trendHistory := Array.concat(store.trendHistory, [point]);
  };

  public func setMembershipDue(store : Store, amount : Nat) {
    store.membershipDue := amount;
  };

  public type Stable = {
    lastPaidEpoch : [(Principal, Nat)];
    trendHistory : [Types.AlignmentTrendPoint];
    membershipDue : Nat;
  };

  public func toStable(store : Store) : Stable {
    {
      lastPaidEpoch = Iter.toArray(Map.entries(store.lastPaidEpoch));
      trendHistory = store.trendHistory;
      membershipDue = store.membershipDue;
    };
  };

  public func fromStable(snapshot : Stable) : Store {
    let store = init(snapshot.membershipDue);
    store.lastPaidEpoch := Map.fromIter(snapshot.lastPaidEpoch.vals(), Principal.compare);
    store.trendHistory := snapshot.trendHistory;
    store;
  };
};
