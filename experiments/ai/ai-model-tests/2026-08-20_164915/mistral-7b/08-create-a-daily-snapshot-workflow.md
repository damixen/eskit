# Test

- **Model:** mistral:7b
- **Question:** Create a daily snapshot workflow.
- **Elapsed time:** 11.732 seconds

## Response

To create a daily snapshot workflow using the provided command structure, we can use the `eskit ilm create` command with specific arguments. Here's a step-by-step guide:

1. First, make sure you have the necessary configuration file (`.eskit/config.json`) set up with your Elasticsearch cluster details.

2. Navigate to your project directory where you have the `eskit` command installed.

3. Run the following command to create a new daily snapshot workflow:

```
eskit ilm create --schedule "0 0 * * *" --order 0 --priority max --alias daily_snapshot --actions create --action-params index=my_index,rollover=alias=previous_day,max_size=5gb,rollover_alias=archive --actions rollover --action-params index=my_index,alias=daily_snapshot,previous_alias=previous_day
```

Let's break down the command:

- `eskit ilm create`: This creates a new lifecycle policy.
- `--schedule "0 0 * * *"`: This sets the schedule for the policy to run daily at midnight.
- `--order 0`: This sets the order of the policy in the list.
- `--priority max`: This sets the policy priority to the maximum value.
- `--alias daily_snapshot`: This sets the alias for the policy.
- `--actions create`: This specifies that a new index will be created according to the action params.
- `--action-params index=my_index,rollover=alias=previous_day,max_size=5gb,rollover_alias=archive`: These params set the name of the index, the rollover alias, the maximum size, and the archive alias for the created index.
- `--actions rollover`: This specifies that an existing index will be rolled over according to the action params.
- `--action-params index=my_index,alias=daily_snapshot,previous_alias=previous_day`: These params set the name of the index and the previous alias for the rollover action.

After running this command, you should have a new daily snapshot workflow set up for your `my_index` index. Adjust the command accordingly to set up snapshots for other indices as needed.
