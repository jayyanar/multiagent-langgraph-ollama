flowchart LR
    Documents[Documents] --> Parse[Parse / Extract]
    Parse --> Retrieve[Retrieve]
    Retrieve --> Reason[Reason]
    Reason --> Act[Act]

    %% Optional human-in-the-loop checkpoints
    Human[Human Review]
    Parse -.-> Human
    Retrieve -.-> Human
    Reason -.-> Human
    Act -.-> Human
