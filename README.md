<div align="center">

# tap-jotform

<div>
  <a href="https://results.pre-commit.ci/latest/github/edgarrmondragon/tap-jotform/main">
    <img alt="pre-commit.ci status" src="https://results.pre-commit.ci/badge/github/edgarrmondragon/tap-jotform/main.svg"/>
  </a>
  <a href="https://github.com/edgarrmondragon/tap-jotform/blob/main/LICENSE">
    <img alt="License" src="https://img.shields.io/github/license/edgarrmondragon/tap-jotform"/>
  </a>
  <a href="https://pypi.org/p/tap-jotform">
    <img alt="License" src="https://img.shields.io/pypi/pyversions/tap-jotform"/>
  </a>
</div>

Singer Tap for Jotform. Built with the [Meltano Singer SDK](https://sdk.meltano.com).

</div>

## Capabilities

* `catalog`
* `state`
* `discover`
* `about`
* `stream-maps`
* `schema-flattening`

## Settings

| Setting             | Required | Default | Description |
|:--------------------|:--------:|:-------:|:------------|
| api_key             | True     | None    | Authentication key. See https://api.jotform.com/docs/#authentication |
| api_url             | False    | https://api.jotform.com | API Base URL |
| user_agent          | False    | tap-jotform/0.0.1 | User-Agent header |
| start_date          | False    | None    | Start date for data collection |
| requests_cache | False    | None    | Cache configuration for HTTP requests |
| stream_maps         | False    | None    | Config object for stream maps capability. For more information check out [Stream Maps](https://sdk.meltano.com/en/latest/stream_maps.html). |
| stream_map_config   | False    | None    | User-defined config values to be used within map expressions. |
| flattening_enabled  | False    | None    | 'True' to enable schema flattening and automatically expand nested properties. |
| flattening_max_depth| False    | None    | The max depth to flatten schemas. |

A full list of supported settings and capabilities is available by running: `tap-jotform --about`

## Streams

| Stream name | API endpoint      | API docs                                       | Notes |
| :---------- | :---------------- | :--------------------------------------------- | :---- |
| forms       | /user/forms       | https://api.jotform.com/docs/#user-forms       | Replication for this stream is opt-in. See instructions [below](#configuring-incremental-replication). |
| questions   | /form/{form_id}/questions | https://api.jotform.com/docs/#form-id-questions | |
| submissions | /user/submissions | https://api.jotform.com/docs/#user-submissions | Replication for this stream is opt-in. See instructions [below](#configuring-incremental-replication).  |
| reports     | /user/reports     | https://api.jotform.com/docs/#user-reports | |
| user_history | /user/history    | https://api.jotform.com/docs/#user-history | |


### Configuring incremental replication

By default, the `forms` and `submissions` stream are synced with `FULL_TABLE` replication. Incremental replication can be enabled by setting the replication metadata in the stream's entry in the catalog file:

* `replication_method`: set to`INCREMENTAL`
* `replication_key` set to `created_at` or `updated_at`. The former will omit updated submissions, while the latter will omit new submissions.

For example, to enable incremental replication for the `submissions` stream:

```json
{
  "streams": [
    {
      "tap_stream_id": "submissions",
      "stream": "submissions",
      "replication_method": "INCREMENTAL",
      "replication_key": "updated_at",
    }
  ]
}
```

### Source Authentication and Authorization

To generate an API key, follow the instructions in https://api.jotform.com/docs/#gettingstarted.

## Usage

You can easily run `tap-jotform` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Tap Directly

```bash
tap-jotform --version
tap-jotform --help
tap-jotform --config CONFIG --discover > ./catalog.json
```

## Developer Resources

### Initialize your Development Environment

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh  # or see https://docs.astral.sh/uv/getting-started/installation/
uv sync
```

### Create and Run Tests

Create tests within the `tap_jotform/tests` subfolder and
  then run:

```bash
uv run pytest
```

You can also test the `tap-jotform` CLI interface directly using `uv run`:

```bash
uv run tap-jotform --help
```

### Testing with [Meltano](https://www.meltano.com)

_**Note:** This tap will work in any Singer environment and does not require Meltano.
Examples here are for convenience and to streamline end-to-end orchestration scenarios._

Your project comes with a custom `meltano.yml` project file already created. Open the `meltano.yml` and follow any _"TODO"_ items listed in
the file.

Next, install Meltano (if you haven't already) and any needed plugins:

```bash
# Install meltano
uv tool install meltano
# Initialize meltano within this directory
cd tap-jotform
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke tap-jotform --version
# OR run a test EL pipeline:
meltano run tap-jotform target-jsonl
```

### SDK Dev Guide

See the [dev guide](https://sdk.meltano.com/en/latest/dev_guide.html) for more instructions on how to use the SDK to
develop your own taps and targets.
