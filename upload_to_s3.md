# Upload Mailbox Raw Data to S3

1. Open a terminal at the repository root.
2. Export the required credentials (adjust values to your environment):
   ```bash
   export S3_ENDPOINT_URL="https://your-endpoint"
   export S3_REGION_NAME="fr-par"
   export SCW_ACCESS_KEY="your_access_key"
   export SCW_SECRET_KEY="your_secret_key"
   ```
   *(Alternatively, place the same variables in a `.env` file.)*
3. Run the uploader with the mailbox raw folder and the S3 prefix you want:
   ```bash
   ./upload_to_s3.py local_data_path mailbox_name
   ```


Once the script finishes, the uploaded data appears automatically inside the Olkoa app for the matching mailbox.
