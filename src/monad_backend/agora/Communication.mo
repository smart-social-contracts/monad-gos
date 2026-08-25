import Types "../ggg/Types";
import Map "mo:core/Map";
import Iter "mo:core/Iter";
import Text "mo:core/Text";
import Array "mo:core/Array";
import Principal "mo:core/Principal";
import Nat "mo:core/Nat";

module {
  public type Store = {
    var nextBroadcastId : Nat;
    var nextThreadId : Nat;
    var nextMessageId : Nat;
    var broadcasts : Map.Map<Types.BroadcastId, Types.BroadcastMessage>;
    var broadcastOrder : [Types.BroadcastId];
    var threads : Map.Map<Types.ThreadId, Types.Thread>;
    var threadParticipants : Map.Map<Types.ThreadId, [Principal]>;
  };

  public func init() : Store {
    {
      var nextBroadcastId = 1;
      var nextThreadId = 1;
      var nextMessageId = 1;
      var broadcasts = Map.empty<Types.BroadcastId, Types.BroadcastMessage>();
      var broadcastOrder = [];
      var threads = Map.empty<Types.ThreadId, Types.Thread>();
      var threadParticipants = Map.empty<Types.ThreadId, [Principal]>();
    };
  };

  func participantList(store : Store, threadId : Types.ThreadId) : [Principal] {
    switch (Map.get(store.threadParticipants, Text.compare, threadId)) {
      case (?participants) participants;
      case null [];
    };
  };

  func addParticipant(store : Store, threadId : Types.ThreadId, participant : Principal) {
    let existing = participantList(store, threadId);
    for (principal in existing.vals()) {
      if (Principal.equal(principal, participant)) {
        return;
      };
    };
    Map.add(store.threadParticipants, Text.compare, threadId, Array.concat(existing, [participant]));
  };

  func participantCount(store : Store, threadId : Types.ThreadId) : Nat {
    participantList(store, threadId).size();
  };

  func isParticipant(store : Store, threadId : Types.ThreadId, caller : Principal) : Bool {
    for (principal in participantList(store, threadId).vals()) {
      if (Principal.equal(principal, caller)) {
        return true;
      };
    };
    false;
  };

  func isMonad(monad : ?Principal, caller : Principal) : Bool {
    switch (monad) {
      case (?principal) Principal.equal(principal, caller);
      case null false;
    };
  };

  func canAccessThread(
    store : Store,
    caller : Principal,
    threadId : Types.ThreadId,
    visibility : Types.ThreadVisibility,
    monad : ?Principal,
  ) : Bool {
    if (visibility == "public") { true } else if (isMonad(monad, caller)) {
      true;
    } else {
      isParticipant(store, threadId, caller);
    };
  };

  func threadSummary(thread : Types.Thread) : Types.ThreadSummary {
    {
      id = thread.id;
      title = thread.title;
      participant_count = thread.participant_count;
      visibility = thread.visibility;
      last_activity_at = thread.updated_at;
      epoch = thread.epoch;
    };
  };

  public func postBroadcast(
    store : Store,
    author : Principal,
    body : Text,
    epoch : Types.EpochId,
  ) : Types.Result_BroadcastId {
    if (Text.size(body) == 0) {
      return #err(#invalid_input("body is required"));
    };
    let id = Types.entityId("broadcast", store.nextBroadcastId);
    store.nextBroadcastId += 1;
    let message : Types.BroadcastMessage = {
      id;
      author = Types.principalId(author);
      body;
      epoch;
      created_at = Types.now();
    };
    Map.add(store.broadcasts, Text.compare, id, message);
    store.broadcastOrder := Array.concat(store.broadcastOrder, [id]);
    #ok(id);
  };

  public func readBroadcast(store : Store) : Types.BroadcastFeed {
    let broadcasts = Array.map<Types.BroadcastId, Types.BroadcastMessage>(
      store.broadcastOrder,
      func (id : Types.BroadcastId) : Types.BroadcastMessage {
        switch (Map.get(store.broadcasts, Text.compare, id)) {
          case (?message) message;
          case null {
            // unreachable for ordered ids
            {
              id;
              author = "";
              body = "";
              epoch = "";
              created_at = 0;
            };
          };
        };
      },
    );
    let publicThreads = Array.filterMap<Types.ThreadId, Types.ThreadSummary>(
      Iter.toArray(Map.keys(store.threads)),
      func (id : Types.ThreadId) : ?Types.ThreadSummary {
        switch (Map.get(store.threads, Text.compare, id)) {
          case (?thread) {
            if (thread.visibility == "public") { ?threadSummary(thread) } else { null };
          };
          case null null;
        };
      },
    );
    { broadcasts; public_threads = publicThreads };
  };

  public func listThreads(store : Store, caller : Principal, monad : ?Principal) : [Types.ThreadSummary] {
    Array.filterMap<Types.ThreadId, Types.ThreadSummary>(
      Iter.toArray(Map.keys(store.threads)),
      func (id : Types.ThreadId) : ?Types.ThreadSummary {
        switch (Map.get(store.threads, Text.compare, id)) {
          case (?thread) {
            if (canAccessThread(store, caller, id, thread.visibility, monad)) {
              ?threadSummary(thread);
            } else {
              null;
            };
          };
          case null null;
        };
      },
    );
  };

  public func readThread(
    store : Store,
    caller : Principal,
    threadId : Types.ThreadId,
    monad : ?Principal,
  ) : ?Types.Thread {
    switch (Map.get(store.threads, Text.compare, threadId)) {
      case null null;
      case (?thread) {
        if (canAccessThread(store, caller, threadId, thread.visibility, monad)) {
          ?thread;
        } else {
          null;
        };
      };
    };
  };

  func titleFromBody(body : Text) : Text {
    if (body.size() <= 48) {
      body;
    } else {
      var result = "";
      var count = 0;
      label chars for (char in body.chars()) {
        if (count >= 48) { break chars };
        result #= Text.fromChar(char);
        count += 1;
      };
      result # "…";
    };
  };

  func createPrivateThread(
    store : Store,
    caller : Principal,
    body : Text,
    epoch : Types.EpochId,
    monad : ?Principal,
    broadcastId : ?Types.BroadcastId,
  ) : Types.Result_ThreadId {
    if (Text.size(body) == 0) {
      return #err(#invalid_input("body is required"));
    };
    let threadId = Types.entityId("thread", store.nextThreadId);
    store.nextThreadId += 1;
    let messageId = Types.entityId("msg", store.nextMessageId);
    store.nextMessageId += 1;
    let timestamp = Types.now();
    let message : Types.ThreadMessage = {
      id = messageId;
      thread_id = threadId;
      author = Types.principalId(caller);
      body;
      created_at = timestamp;
    };
    addParticipant(store, threadId, caller);
    switch (monad) {
      case (?principal) addParticipant(store, threadId, principal);
      case null {};
    };
    let thread : Types.Thread = {
      id = threadId;
      title = titleFromBody(body);
      visibility = "private";
      participant_count = participantCount(store, threadId);
      epoch;
      broadcast_id = broadcastId;
      messages = [message];
      created_at = timestamp;
      updated_at = timestamp;
    };
    Map.add(store.threads, Text.compare, threadId, thread);
    #ok(threadId);
  };

  public func replyToBroadcast(
    store : Store,
    caller : Principal,
    broadcastId : Types.BroadcastId,
    body : Text,
    epoch : Types.EpochId,
    monad : ?Principal,
  ) : Types.Result_ThreadId {
    switch (Map.get(store.broadcasts, Text.compare, broadcastId)) {
      case null return #err(#not_found);
      case (?_) {};
    };
    createPrivateThread(store, caller, body, epoch, monad, ?broadcastId);
  };

  public func startThread(
    store : Store,
    caller : Principal,
    body : Text,
    epoch : Types.EpochId,
    monad : ?Principal,
  ) : Types.Result_ThreadId {
    createPrivateThread(store, caller, body, epoch, monad, null);
  };

  public func replyToThread(
    store : Store,
    caller : Principal,
    threadId : Types.ThreadId,
    body : Text,
    monad : ?Principal,
  ) : Types.Result_ThreadMessageId {
    if (Text.size(body) == 0) {
      return #err(#invalid_input("body is required"));
    };
    switch (Map.get(store.threads, Text.compare, threadId)) {
      case null return #err(#not_found);
      case (?thread) {
        switch (thread.visibility) {
          case ("private") {
            if (not canAccessThread(store, caller, threadId, thread.visibility, monad)) {
              return #err(#unauthorized);
            };
          };
          case ("public") {};
          case (_) return #err(#invalid_input("invalid thread visibility"));
        };

        let messageId = Types.entityId("msg", store.nextMessageId);
        store.nextMessageId += 1;
        let timestamp = Types.now();
        let message : Types.ThreadMessage = {
          id = messageId;
          thread_id = threadId;
          author = Types.principalId(caller);
          body;
          created_at = timestamp;
        };
        addParticipant(store, threadId, caller);
        let updated : Types.Thread = {
          thread with
          messages = Array.concat(thread.messages, [message]);
          participant_count = participantCount(store, threadId);
          updated_at = timestamp;
        };
        Map.add(store.threads, Text.compare, threadId, updated);
        #ok(messageId);
      };
    };
  };

  public type Stable = {
    nextBroadcastId : Nat;
    nextThreadId : Nat;
    nextMessageId : Nat;
    broadcasts : [(Types.BroadcastId, Types.BroadcastMessage)];
    broadcastOrder : [Types.BroadcastId];
    threads : [(Types.ThreadId, Types.Thread)];
    threadParticipants : [(Types.ThreadId, [Principal])];
  };

  public func toStable(store : Store) : Stable {
    {
      nextBroadcastId = store.nextBroadcastId;
      nextThreadId = store.nextThreadId;
      nextMessageId = store.nextMessageId;
      broadcasts = Iter.toArray(Map.entries(store.broadcasts));
      broadcastOrder = store.broadcastOrder;
      threads = Iter.toArray(Map.entries(store.threads));
      threadParticipants = Iter.toArray(Map.entries(store.threadParticipants));
    };
  };

  public func fromStable(snapshot : Stable) : Store {
    let store = init();
    store.nextBroadcastId := snapshot.nextBroadcastId;
    store.nextThreadId := snapshot.nextThreadId;
    store.nextMessageId := snapshot.nextMessageId;
    store.broadcasts := Map.fromIter(snapshot.broadcasts.vals(), Text.compare);
    store.broadcastOrder := snapshot.broadcastOrder;
    store.threads := Map.fromIter(snapshot.threads.vals(), Text.compare);
    store.threadParticipants := Map.fromIter(snapshot.threadParticipants.vals(), Text.compare);
    store;
  };
};
