# TimeSpace-AI

The required packages needed to run TimeSpace-AI are included in the ***requirements.txt*** file.

They can be installed by using the command:

``` pip install -r requirements.txt ```

Other packages can be installed using `pip3 install ...` command.

## System Architecture
```mermaid
flowchart TD
    A[Orchestrator Agent] -->|Triggers GCal Scraping Task| C(Google Calendar Scraper)
    A[Orchestrator Agent] -->|Triggers Initialization of New Event| D(Event Initializer)
    A[Orchestrator Agent] -->|Triggers Update in Existing Event| E(Event Editor)
    
    B(Google Calendar Service)
    C -->|Authenticate| B
    D -->|Authenticate| B
    E -->|Authenticate| B
```
