/// GGG wire types aligned with `/srv/dev/ggg/ggg.did` v0.2.0.
import Principal "mo:core/Principal";
import Nat "mo:core/Nat";
import Nat64 "mo:core/Nat64";
import Time "mo:core/Time";
import Text "mo:core/Text";

module {
  public type PrincipalId = Text;
  public type EntityId = Text;
  public type Timestamp = Nat64;
  public type IsoTimestamp = Text;
  public type Metadata = Text;

  public type GggError = {
    #not_found;
    #unauthorized;
    #invalid_input : Text;
    #conflict : Text;
    #forbidden : Text;
  };

  public type Result = { #ok; #err : GggError };

  /// Validated domain tag (Candid `text` on the wire; see ggg.did).
  public type Domain = Text;

  public let DOMAIN_TAGS : [Domain] = [
    "identity",
    "governance",
    "finance",
    "justice",
    "land",
    "system",
  ];

  public func validateDomain(domain : Domain) : ?GggError {
    for (tag in DOMAIN_TAGS.vals()) {
      if (domain == tag) {
        return null;
      };
    };
    ?#invalid_input("invalid domain tag");
  };

  public type WishId = EntityId;
  public type EpochId = Text;

  public type Wish = {
    id : WishId;
    author : PrincipalId;
    domain : Domain;
    ciphertext : Text;
    epoch : EpochId;
    assistant_id : Text;
    created_at : Timestamp;
  };

  public type ProposalId = EntityId;

  public type ProposalStatus = {
    #pending_vote;
    #voting;
    #approved;
    #rejected;
    #no_quorum;
    #expired;
  };

  public type Proposal = {
    id : ProposalId;
    title : Text;
    description : Text;
    code_url : Text;
    code_checksum : Text;
    proposer : PrincipalId;
    status : ProposalStatus;
    voting_deadline : ?IsoTimestamp;
    votes_yes : Nat;
    votes_no : Nat;
    votes_abstain : Nat;
    total_voters : Nat;
    required_threshold : Float;
    org_scope : Text;
    metadata : Metadata;
    created_at : Timestamp;
    updated_at : Timestamp;
  };

  public type VoteId = EntityId;

  public type VoteChoice = { #yes; #no; #abstain };

  public type Vote = {
    id : VoteId;
    proposal_id : ProposalId;
    voter : PrincipalId;
    choice : VoteChoice;
    metadata : Metadata;
    created_at : Timestamp;
  };

  public type BroadcastId = EntityId;
  public type ThreadId = EntityId;
  public type ThreadMessageId = EntityId;

  public type BroadcastMessage = {
    id : BroadcastId;
    author : PrincipalId;
    body : Text;
    epoch : EpochId;
    created_at : Timestamp;
  };

  public type ThreadVisibility = Text;

  public let THREAD_VISIBILITY_TAGS : [ThreadVisibility] = ["private", "public"];

  public func validateThreadVisibility(visibility : ThreadVisibility) : ?GggError {
    for (tag in THREAD_VISIBILITY_TAGS.vals()) {
      if (visibility == tag) {
        return null;
      };
    };
    ?#invalid_input("invalid thread visibility");
  };

  public type ThreadSummary = {
    id : ThreadId;
    title : Text;
    participant_count : Nat;
    visibility : ThreadVisibility;
    last_activity_at : Timestamp;
    epoch : EpochId;
  };

  public type BroadcastFeed = {
    broadcasts : [BroadcastMessage];
    public_threads : [ThreadSummary];
  };

  public type ThreadMessage = {
    id : ThreadMessageId;
    thread_id : ThreadId;
    author : PrincipalId;
    body : Text;
    created_at : Timestamp;
  };

  public type Thread = {
    id : ThreadId;
    title : Text;
    visibility : ThreadVisibility;
    participant_count : Nat;
    epoch : EpochId;
    broadcast_id : ?BroadcastId;
    messages : [ThreadMessage];
    created_at : Timestamp;
    updated_at : Timestamp;
  };

  public type EpochPhase = {
    #converse;
    #sealed;
    #deliberate;
    #ratify;
    #execute;
  };

  public type EpochStatus = {
    epoch_id : EpochId;
    phase : EpochPhase;
    seal_at : Timestamp;
    seconds_until_seal : Nat;
  };

  public type AlignmentCoefficient = {
    coefficient : Float;
    citizens_total : Nat;
    citizens_current : Nat;
    membership_due : Nat;
    as_of : Timestamp;
  };

  public type AlignmentTrendPoint = {
    epoch : EpochId;
    coefficient : Float;
    as_of : Timestamp;
  };

  public type SubmitWishInput = {
    domain : Domain;
    ciphertext : Text;
    epoch : EpochId;
    assistant_id : Text;
  };

  public type SubmitProposalInput = {
    title : Text;
    description : Text;
    code_url : Text;
    code_checksum : Text;
    voting_deadline : ?IsoTimestamp;
    required_threshold : ?Float;
    org_scope : Text;
    metadata : Metadata;
  };

  public type CastVoteInput = {
    proposal_id : ProposalId;
    choice : VoteChoice;
    metadata : Metadata;
  };

  public type ProposalFilter = {
    status : ?ProposalStatus;
    org_scope : ?Text;
    limit : Nat;
    offset : Nat;
  };

  public type Result_WishId = { #ok : WishId; #err : GggError };
  public type Result_ProposalId = { #ok : ProposalId; #err : GggError };
  public type Result_VoteId = { #ok : VoteId; #err : GggError };
  public type Result_ThreadId = { #ok : ThreadId; #err : GggError };
  public type Result_ThreadMessageId = { #ok : ThreadMessageId; #err : GggError };
  public type Result_BroadcastId = { #ok : BroadcastId; #err : GggError };

  public let GGG_VERSION : Text = "0.2.0";

  public func principalId(principal : Principal) : PrincipalId {
    Principal.toText(principal);
  };

  public func entityId(prefix : Text, counter : Nat) : EntityId {
    prefix # "-" # Nat.toText(counter);
  };

  public func epochId(counter : Nat) : EpochId {
    Nat.toText(counter);
  };

  public func now() : Timestamp {
    Nat64.fromIntWrap(Time.now() / 1_000_000_000);
  };
};
