---
# Copyright Vespa.ai. All rights reserved.
title: "Inspecting structured data in a Searcher"
---

The [Data Access API](https://javadoc.io/doc/com.yahoo.vespa/vespajlib/latest/com/yahoo/data/access/package-summary.html) is used to access structured data such as arrays and weighted sets.

## Use Case: accessing array attributes

The following illustrates accessing some field that is of array type:

```
{% highlight java %}
import com.yahoo.search.*;
import com.yahoo.search.result.*;
import com.yahoo.search.searchchain.*;
import com.yahoo.data.access.*;

@After(PhaseNames.TRANSFORMED_QUERY)
@Before(PhaseNames.BLENDED_RESULT)
public class SimpleTestSearcher extends Searcher {

    public Result search(Query query, Execution execution) {
        Result r = execution.search(query);
        execution.fill(r);
        for (Hit hit : r.hits().asList()) {
            if (hit.isMeta()) continue;
            Object o = hit.getField("titles");
            if (o instanceof Inspectable) {
                StringBuilder pasteBuf = new StringBuilder();
                Inspectable field = (Inspectable) o;
                Inspector arr = field.inspect();
                for (int i = 0; i < arr.entryCount(); i++) {
                    pasteBuf.append(arr.entry(i).asString(""));
                    if (i+1 < arr.entryCount()) {
                        pasteBuf.append(", ");
                    }
                }
                hit.setField("titles", pasteBuf.toString());
            }
        }
        return r;
    }
}
{% endhighlight %}
```

Here we assume there is a field in our schema like this:

```
field titles type array<string> {
    indexing: attribute | summary
}
```

Again we process each hit, this time traversing the array and building a string which contains all the titles,
transforming a field looking like this:

```
{% highlight json %}
 "titles": [
            "Bond",
            "James Bond"
]
{% endhighlight %}
```

into this output:

```
{% highlight json %}
"titles": "Bond, James Bond"
{% endhighlight %}
```

## Use Case: accessing weighted set attributes

The following example illustrates accessing data held in a weighted set.
Note that the Data Access API doesn't have a "set" or "weighted set" concept;
the weighted set is represented as an unordered array of objects
where each object has an "item" and a "weight" field.
The weight is a long integer value,
while the item type will vary according to the field type as declared in the schema.

```
{% highlight java %}
import com.yahoo.search.*;
import com.yahoo.search.result.*;
import com.yahoo.search.searchchain.*;
import com.yahoo.data.access.*;

@After(PhaseNames.TRANSFORMED_QUERY)
@Before(PhaseNames.BLENDED_RESULT)
public class SimpleTestSearcher extends Searcher {

    public Result search(Query query, Execution execution) {
        Result r = execution.search(query);
        execution.fill(r);
        for (Hit hit : r.hits().asList()) {
            processHit(hit);
        }
        return r;
    }

    void processHit(Hit hit) {
        if (hit.isMeta()) return;
        Object o = hit.getField("titles");
        if (o instanceof Inspectable) {
            StringBuilder pasteBuf = new StringBuilder();
            Inspectable field = (Inspectable) o;
            Inspector arr = field.inspect();
            for (int i = 0; i < arr.entryCount(); i++) {
                String sval = arr.entry(i).field("item").asString("");
                long weight = arr.entry(i).field("weight").asLong(0);
                pasteBuf.append("title: ");
                pasteBuf.append(sval);
                pasteBuf.append("[");
                pasteBuf.append(weight);
                pasteBuf.append("]");
                if (i+1 < arr.entryCount()) {
                    pasteBuf.append(", ");
                }
            }
            hit.setField("alternates", pasteBuf.toString());
        }
    }

}
{% endhighlight %}
```

Here we assume there is a field in the schema like:

```
field titles type weightedset<string> {
    indexing: attribute | summary
}
```

Again we process each hit, and format each element of the weighted set, transforming this input:

```
{% highlight json %}
"titles": {
            "Bond": 15,
            "James Bond": 89
}
{% endhighlight %}
```

into this output:

```
{% highlight json %}
"alternates": "title: Bond[15], title: James Bond[89]"
{% endhighlight %}
```

## Unit testing with structured data

For unit testing it is useful to be able to create structured data fields programmatically.
This case be done using `Slime`:

```
{% highlight java %}
import com.yahoo.slime.*;
import com.yahoo.data.access.slime.SlimeAdapter;

// Struct example:
Slime slime = new Slime();
Cursor struct = slime.setObject();
struct.setString("foo", "bar");
struct.setDouble("number", 1.0);
myHit.setField("mystruct", new SlimeAdapter(struct));

// Array example:
Slime slime = new Slime();
Cursor array = slime.setArray();
array.addString("foo");
array.addString("bar");
myHit.setField("myarray", new SlimeAdapter(array));

// Arrays and objects can be arbitrarily nested

// Alternatively, create the slime structure from a JSON string:
Slime slime = SlimeUtils.jsonToSlime(myJsonString.getBytes(StandardCharsets.UTF_8));
myHit.setField("myfield", new SlimeAdapter(slime.get()));
{% endhighlight %}
```
