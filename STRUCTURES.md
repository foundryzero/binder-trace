# 📦 Structures

You may find that when running binder_trace some of the structures don't quite match those of your particular device or emulator version. Unfortunately this is a difficult problem to solve. The interfaces and parcelable structures used by binder only need to be internally consistent within a single build of Android. That is to say they don't need to be backwards or forwards compatible with other versions. To see why this is an issue consider this example AIDL interface.

```java
interface IRemoteService {
    int getPid();
    String getName()
}
```

When AOSP is compiled each method in the interface is assigned a number based on the order they are defined. So in this case, getPid is number 0 and getName is number 1. These are the numbers that you see listed in the main transactions window when running binder_trace. We're mapping these back to their original function names based on the version of the interface in the AOSP build we generated the structures against.

Now imagine someone adds a new feature to `IRemoteService`. They think its important so they put it right at the top of the interface.

```java
interface IRemoteService {
    int getId();
    int getPid();
    String getName()
}
```

Now when this interface is compiled the new `getId` method is number 1, `getPid` and `getName` have been bumped up to 2 and 3 respectively. The binder_trace structures generated for either version would be incompatible with the other. We'd have the same issue if a method was removed from the interface. There is a similar problem with arguments to methods and members in parcelable structures. If they are added or removed the resulting data structures become incompatible.

Unfortunately this means that we can't necessarily improve compatibility with your device by just updating the structures to the latest version. What's matters is trying to get a set of structures as close to your build version as possible. Therefore you have a few options.

* You can wait until we generate a new set of structures and see if they're any better. We'll to do this periodically and when there is a significant change, like a new major version.

* If you know what version of AOSP you're device is based on (or close to) you can raise a ticket and we'll try to generate structures for that verison.
What we'd need is the tag you're interested in from the list of [AOSP tags and builds](https://source.android.com/docs/setup/about/build-numbers#source-code-tags-and-builds). We can't make any commitments or guarantees as to when we'll be able to do this, but we respond well to politeness and flattery 😉

* You can try modify the structures yourself. If there have been significant changes this probably isn't feasible, but if you know that the method numbering has got out of sync due to a method being added or removed you might be able to fix up the call numbers in the structure files.

Luckily the vast majority of interfaces and data types and pretty stable, so although 100% accuracy probably isn't achievable, hopefully the result you get will be good enough to support you research.