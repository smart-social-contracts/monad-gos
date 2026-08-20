import Types "./ggg/Types";
import Wishes "./agora/Wishes";
import Communication "./agora/Communication";
import Alignment "./alignment/Coefficient";
import Grammar "./grammar/Validator";
import Codex "./codex/codex";
import Map "mo:core/Map";
import Iter "mo:core/Iter";
import Array "mo:core/Array";
import Text "mo:core/Text";
import Principal "mo:core/Principal";
import Nat "mo:core/Nat";
import Nat64 "mo:core/Nat64";
import Int "mo:core/Int";
import Time "mo:core/Time";

persistent actor {
  stable var stableAgora : Wishes.Stable = {
    currentEpoch = 0;
    nextWishId = 1;
    wishes = [];
    wishesByEpoch = [];
    sealedEpochs = [];
  };
  stable var stableAlignment : Alignment.Stable = {
    lastPaidEpoch = [];
    trendHistory = [];
    membershipDue = 12;
  };
  stable var stableCommunication : Communication.Stable = {
    nextBroadcastId = 1;
    nextThreadId = 1;
    nextMessageId = 1;
    broadcasts = [];
    broadcastOrder = [];
    threads = [];
    threadParticipants = [];
  };
  stable var stableProposals : [(Types.ProposalId, Types.Proposal)] = [];
  stable var stableVotes : [(Types.VoteId, Types.Vote)] = [];
  stable var stableVoteKeys : [(Text, Types.VoteId)] = [];
  stable var stableProposalOrder : [Types.ProposalId] = [];
  stable var nextProposalId : Nat = 1;
  stable var nextVoteId : Nat = 1;
  stable var monadPrincipal : ?Principal = null;
  stable var monadFrozen : Bool = false;
  stable var adminPrincipal : ?Principal = null;
  stable var grammarSpendCap : Nat = 1_000_000;
  stable var grammarForbiddenOps : [Text] = ["mint_unbounded", "seize_all", "revoke_all_mandates"];
  stable var epochPhase : Types.EpochPhase = #converse;
  stable var sealAt : Types.Timestamp = 0;
  stable var stableReplyInputs : [(Types.ThreadMessageId, Types.ReplyInputs)] = [];
  stable var stableCodex : Codex.Stable = {
    treasuryBalance = 0;
    createdAt = 0;
    updatedAt = 0;
    lines = [];
    commit = "";
  };
  stable var nextMcpPairing : Nat = 1;
  stable var stableMcpPairings : [(Text, { principal : Principal; expires_at : Int })] = [];

  type McpPairing = { principal : Principal; expires_at : Int };

  let mcpPairingTtlNs : Int = 600_000_000_000;

  var agora = Wishes.fromStable(stableAgora);
  var alignmentStore = Alignment.fromStable(stableAlignment);
  var communication = Communication.fromStable(stableCommunication);
  var proposals = Map.fromIter<Types.ProposalId, Types.Proposal>(stableProposals.vals(), Text.compare);
  var votes = Map.fromIter<Types.VoteId, Types.Vote>(stableVotes.vals(), Text.compare);
  var voteKeys = Map.fromIter<Text, Types.VoteId>(stableVoteKeys.vals(), Text.compare);
  var proposalOrder : [Types.ProposalId] = stableProposalOrder;
  var replyInputsStore = Map.fromIter<Types.ThreadMessageId, Types.ReplyInputs>(
    stableReplyInputs.vals(),
    Text.compare,
  );
  var mcpPairings = Map.fromIter<Text, McpPairing>(stableMcpPairings.vals(), Text.compare);
  var codexStore = Codex.fromStable(stableCodex);

  system func preupgrade() {
    stableAgora := Wishes.toStable(agora);
    stableAlignment := Alignment.toStable(alignmentStore);
    stableCommunication := Communication.toStable(communication);
    stableProposals := Iter.toArray(Map.entries(proposals));
    stableVotes := Iter.toArray(Map.entries(votes));
    stableVoteKeys := Iter.toArray(Map.entries(voteKeys));
    stableProposalOrder := proposalOrder;
    stableReplyInputs := Iter.toArray(Map.entries(replyInputsStore));
    stableMcpPairings := Iter.toArray(Map.entries(mcpPairings));
    stableCodex := Codex.toStable(codexStore);
  };

  func grammarConfig() : Grammar.Config {
    {
      spend_cap = grammarSpendCap;
      forbidden_operations = grammarForbiddenOps;
    };
  };

  func requireAdmin(caller : Principal) : ?Types.GggError {
    switch (adminPrincipal) {
      case (?admin) {
        if (Principal.equal(caller, admin)) { null } else { ?#unauthorized };
      };
      case null ?#forbidden("admin is not bootstrapped");
    };
  };

  func requireMonad(caller : Principal) : ?Types.GggError {
    if (monadFrozen) {
      return ?#forbidden("monad is frozen");
    };
    switch (monadPrincipal) {
      case (?principal) {
        if (Principal.equal(caller, principal)) { null } else { ?#unauthorized };
      };
      case null ?#forbidden("monad principal is not set");
    };
  };

  func converseOpen() : Bool {
    epochPhase == #converse and not Wishes.isEpochSealed(agora, Wishes.currentEpochId(agora));
  };

  func secondsUntilSeal() : Nat {
    if (epochPhase != #converse) {
      return 0;
    };
    let now = Types.now();
    if (now >= sealAt) {
      0;
    } else {
      Nat64.toNat(sealAt - now);
    };
  };

  func ensureSealSchedule() {
    if (sealAt == 0) {
      sealAt := Types.now() + 86_400;
    };
  };

  func voteKey(proposalId : Types.ProposalId, voter : Types.PrincipalId) : Text {
    proposalId # "|" # voter;
  };

  func removePairingsForPrincipal(principal : Principal) {
    let codesToRemove = Array.filterMap<(Text, McpPairing), Text>(
      Iter.toArray(Map.entries(mcpPairings)),
      func ((code, pairing) : (Text, McpPairing)) : ?Text {
        if (Principal.equal(pairing.principal, principal)) { ?code } else { null };
      },
    );
    for (code in codesToRemove.vals()) {
      Map.remove(mcpPairings, Text.compare, code);
    };
  };

  func matchesFilter(proposal : Types.Proposal, filter : Types.ProposalFilter) : Bool {
    let statusOk = switch (filter.status) {
      case (?status) proposal.status == status;
      case null true;
    };
    let scopeOk = switch (filter.org_scope) {
      case (?scope) proposal.org_scope == scope;
      case null true;
    };
    statusOk and scopeOk;
  };

  public query func ggg_version() : async Text {
    Types.GGG_VERSION;
  };

  public query func current_epoch() : async Types.EpochId {
    Wishes.currentEpochId(agora);
  };

  public shared ({ caller }) func submit_wish(input : Types.SubmitWishInput) : async Types.Result_WishId {
    if (not converseOpen()) {
      return #err(#forbidden("epoch is not open for wishes"));
    };
    Wishes.submit(agora, caller, input);
  };

  public query func get_wish(id : Types.WishId) : async ?Types.Wish {
    Wishes.get(agora, id);
  };

  public query func list_wishes_by_epoch(epoch : Types.EpochId) : async [Types.Wish] {
    Wishes.listByEpoch(agora, epoch);
  };

  public shared ({ caller }) func seal_epoch() : async Types.Result {
    switch (requireAdmin(caller)) {
      case (?err) #err(err);
      case null {
        switch (Wishes.seal(agora)) {
          case (#ok(_)) {
            Alignment.snapshotEpoch(alignmentStore, agora.currentEpoch - 1);
            epochPhase := #sealed;
            #ok;
          };
          case (#err(err)) #err(err);
        };
      };
    };
  };

  public shared ({ caller }) func record_due_payment() : async () {
    Alignment.recordDuePayment(alignmentStore, caller, agora.currentEpoch);
    Codex.creditDues(codexStore, alignmentStore.membershipDue);
  };

  public query func get_treasury(name : Types.TreasuryName) : async ?Types.Treasury {
    if (name != Codex.TREASURY_NAME) {
      return null;
    };
    ?Codex.treasury(codexStore);
  };

  public query func get_realm_state() : async Codex.RealmState {
    Codex.snapshot(
      codexStore,
      alignmentStore.membershipDue,
      Alignment.compute(alignmentStore, agora.currentEpoch),
      Wishes.currentEpochId(agora),
    );
  };

  public shared ({ caller }) func set_codex_commit(commit : Text) : async Types.Result {
    switch (requireMonad(caller)) {
      case (?err) #err(err);
      case null {
        if (Text.size(commit) == 0) {
          return #err(#invalid_input("commit is required"));
        };
        Codex.setCommit(codexStore, commit);
        #ok;
      };
    };
  };

  public shared ({ caller }) func codex_spend(line : Text, amount : Nat) : async Types.Result {
    switch (requireMonad(caller)) {
      case (?err) #err(err);
      case null Codex.spend(codexStore, line, amount);
    };
  };

  public query func alignment_coefficient() : async Types.AlignmentCoefficient {
    Alignment.compute(alignmentStore, agora.currentEpoch);
  };

  public query func alignment_trend() : async [Types.AlignmentTrendPoint] {
    Alignment.trend(alignmentStore);
  };

  public query func get_epoch_status() : async Types.EpochStatus {
    ensureSealSchedule();
    {
      epoch_id = Wishes.currentEpochId(agora);
      phase = epochPhase;
      seal_at = sealAt;
      seconds_until_seal = secondsUntilSeal();
    };
  };

  public query func read_broadcast() : async Types.BroadcastFeed {
    Communication.readBroadcast(communication);
  };

  public shared query ({ caller }) func list_threads() : async [Types.ThreadSummary] {
    Communication.listThreads(communication, caller, monadPrincipal);
  };

  public shared query ({ caller }) func read_thread(threadId : Types.ThreadId) : async ?Types.Thread {
    Communication.readThread(communication, caller, threadId, monadPrincipal);
  };

  public shared ({ caller }) func reply_to_broadcast(
    broadcastId : Types.BroadcastId,
    body : Text,
  ) : async Types.Result_ThreadId {
    if (not converseOpen()) {
      return #err(#forbidden("epoch is not open for thread replies"));
    };
    Communication.replyToBroadcast(
      communication,
      caller,
      broadcastId,
      body,
      Wishes.currentEpochId(agora),
      monadPrincipal,
    );
  };

  public shared ({ caller }) func reply_to_thread(
    threadId : Types.ThreadId,
    body : Text,
  ) : async Types.Result_ThreadMessageId {
    if (not converseOpen()) {
      return #err(#forbidden("epoch is not open for thread replies"));
    };
    Communication.replyToThread(communication, caller, threadId, body, monadPrincipal);
  };

  public shared query ({ caller }) func get_reply_inputs(
    messageId : Types.ThreadMessageId,
  ) : async ?Types.ReplyInputs {
    switch (Map.get(replyInputsStore, Text.compare, messageId)) {
      case null null;
      case (?inputs) {
        if (inputs.kind == "broadcast") {
          ?inputs;
        } else {
          switch (
            Communication.readThread(communication, caller, inputs.thread_id, monadPrincipal)
          ) {
            case null null;
            case (?_) ?inputs;
          };
        };
      };
    };
  };

  public shared ({ caller }) func record_reply_inputs(
    inputs : Types.ReplyInputs,
  ) : async Types.Result {
    switch (requireMonad(caller)) {
      case (?err) #err(err);
      case null {
        if (Text.size(inputs.message_id) == 0) {
          return #err(#invalid_input("message_id is required"));
        };
        if (Text.size(inputs.prompt) == 0) {
          return #err(#invalid_input("prompt is required"));
        };
        let stored : Types.ReplyInputs = {
          inputs with created_at = Types.now();
        };
        Map.add(replyInputsStore, Text.compare, inputs.message_id, stored);
        #ok;
      };
    };
  };

  public shared ({ caller }) func post_broadcast(body : Text) : async Types.Result_BroadcastId {
    switch (requireMonad(caller)) {
      case (?err) #err(err);
      case null {
        Communication.postBroadcast(
          communication,
          caller,
          body,
          Wishes.currentEpochId(agora),
        );
      };
    };
  };

  public shared ({ caller }) func bootstrap_admin() : async Types.Result {
    switch (adminPrincipal) {
      case (?_) #err(#conflict("admin already set"));
      case null {
        adminPrincipal := ?caller;
        ensureSealSchedule();
        #ok;
      };
    };
  };

  public shared ({ caller }) func set_monad_principal(principal : Principal) : async Types.Result {
    switch (requireAdmin(caller)) {
      case (?err) #err(err);
      case null {
        monadPrincipal := ?principal;
        #ok;
      };
    };
  };

  public shared ({ caller }) func freeze_monad() : async Types.Result {
    switch (requireAdmin(caller)) {
      case (?err) #err(err);
      case null {
        monadFrozen := true;
        #ok;
      };
    };
  };

  public query func monad_frozen() : async Bool {
    monadFrozen;
  };

  public shared ({ caller }) func submit_proposal(input : Types.SubmitProposalInput) : async Types.Result_ProposalId {
    switch (requireMonad(caller)) {
      case (?err) #err(err);
      case null {
        switch (Grammar.validateInput(grammarConfig(), input)) {
          case (#err(err)) #err(err);
          case (#ok) {
            let id = Types.entityId("proposal", nextProposalId);
            nextProposalId += 1;
            let timestamp = Types.now();
            let proposal : Types.Proposal = {
              id;
              title = input.title;
              description = input.description;
              code_url = input.code_url;
              code_checksum = input.code_checksum;
              proposer = Types.principalId(caller);
              status = #pending_vote;
              voting_deadline = input.voting_deadline;
              votes_yes = 0;
              votes_no = 0;
              votes_abstain = 0;
              total_voters = 0;
              required_threshold = switch (input.required_threshold) {
                case (?threshold) threshold;
                case null 0.5;
              };
              org_scope = input.org_scope;
              metadata = input.metadata;
              created_at = timestamp;
              updated_at = timestamp;
            };
            Map.add(proposals, Text.compare, id, proposal);
            proposalOrder := Array.concat(proposalOrder, [id]);
            #ok(id);
          };
        };
      };
    };
  };

  public query func get_proposal(id : Types.ProposalId) : async ?Types.Proposal {
    Map.get(proposals, Text.compare, id);
  };

  public query func list_proposals(filter : Types.ProposalFilter) : async [Types.Proposal] {
    let matched = Array.filterMap<Types.ProposalId, Types.Proposal>(
      proposalOrder,
      func (id : Types.ProposalId) : ?Types.Proposal {
        switch (Map.get(proposals, Text.compare, id)) {
          case (?proposal) {
            if (matchesFilter(proposal, filter)) { ?proposal } else { null };
          };
          case null null;
        };
      },
    );
    let end = Nat.min(filter.offset + filter.limit, matched.size());
    if (filter.offset >= matched.size()) {
      [];
    } else {
      Array.tabulate(
        end - filter.offset,
        func (index : Nat) : Types.Proposal { matched[filter.offset + index] },
      );
    };
  };

  public shared ({ caller }) func cast_vote(input : Types.CastVoteInput) : async Types.Result_VoteId {
    switch (Map.get(proposals, Text.compare, input.proposal_id)) {
      case null #err(#not_found);
      case (?proposal) {
        let key = voteKey(input.proposal_id, Types.principalId(caller));
        switch (Map.get(voteKeys, Text.compare, key)) {
          case (?_) #err(#conflict("voter already cast on this proposal"));
          case null {
            let voteId = Types.entityId("vote", nextVoteId);
            nextVoteId += 1;
            let vote : Types.Vote = {
              id = voteId;
              proposal_id = input.proposal_id;
              voter = Types.principalId(caller);
              choice = input.choice;
              metadata = input.metadata;
              created_at = Types.now();
            };
            Map.add(votes, Text.compare, voteId, vote);
            Map.add(voteKeys, Text.compare, key, voteId);

            let (yes, no, abstain) = switch (input.choice) {
              case (#yes) (proposal.votes_yes + 1, proposal.votes_no, proposal.votes_abstain);
              case (#no) (proposal.votes_yes, proposal.votes_no + 1, proposal.votes_abstain);
              case (#abstain) (proposal.votes_yes, proposal.votes_no, proposal.votes_abstain + 1);
            };
            let updated : Types.Proposal = {
              proposal with
              votes_yes = yes;
              votes_no = no;
              votes_abstain = abstain;
              total_voters = proposal.total_voters + 1;
              updated_at = Types.now();
              status = if (proposal.status == #pending_vote) { #voting } else { proposal.status };
            };
            Map.add(proposals, Text.compare, input.proposal_id, updated);
            #ok(voteId);
          };
        };
      };
    };
  };

  public query func get_vote(id : Types.VoteId) : async ?Types.Vote {
    Map.get(votes, Text.compare, id);
  };

  public query func validate_proposal(input : Types.SubmitProposalInput) : async Types.Result {
    Grammar.validateInput(grammarConfig(), input);
  };

  public shared ({ caller }) func create_mcp_pairing() : async Types.Result_Text {
    if (Principal.isAnonymous(caller)) {
      return #err(#unauthorized);
    };
    removePairingsForPrincipal(caller);
    let code = "mcp_" # Nat.toText(nextMcpPairing) # "_" # Nat.toText(Int.abs(Time.now()));
    nextMcpPairing += 1;
    let pairing : McpPairing = {
      principal = caller;
      expires_at = Time.now() + mcpPairingTtlNs;
    };
    Map.add(mcpPairings, Text.compare, code, pairing);
    #ok(code);
  };

  public query func verify_mcp_pairing(code : Text) : async ?Text {
    switch (Map.get(mcpPairings, Text.compare, code)) {
      case null null;
      case (?pairing) {
        if (Time.now() >= pairing.expires_at) {
          null;
        } else {
          ?Principal.toText(pairing.principal);
        };
      };
    };
  };
};
