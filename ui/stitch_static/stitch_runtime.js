
(function () {
  const routes = [
    ['dashboard', 'Dashboard', '\u4eea\u8868\u76d8', 'dashboard', '/stitch-static/dashboard_global/code.html'],
    ['collection_tasks', 'Collection Tasks', '\u91c7\u96c6\u4efb\u52a1', 'assignment_turned_in', '/stitch-static/collection_tasks_global/code.html'],
    ['store_coverage', 'Store Coverage', '\u95e8\u5e97\u8986\u76d6', 'storefront', '/stitch-static/store_coverage_global/code.html'],
    ['review_workbench', 'Review Workbench', '\u8bc4\u8bba\u5de5\u4f5c\u53f0', 'rate_review', '/stitch-static/review_workbench_global/code.html'],
    ['platform_matrix', 'Platform Matrix', '\u5e73\u53f0\u77e9\u9635', 'grid_view', '/stitch-static/platform_matrix_global/code.html'],
    ['quality_report', 'Quality Report', '\u8d28\u91cf\u62a5\u544a', 'analytics', '/stitch-static/quality_report_global/code.html'],
    ['safety_audit', 'Safety & Audit', '\u5b89\u5168\u5ba1\u8ba1', 'security', '/stitch-static/safety_audit_global/code.html']
  ];  const timezones = [
    ['Asia/Shanghai', 'Beijing / \u5317\u4eac'],
    ['US/Eastern', 'Washington DC / \u534e\u76db\u987f'],
    ['Asia/Hong_Kong', 'China Hong Kong / \u4e2d\u56fd\u9999\u6e2f'],
    ['Asia/Singapore', 'Singapore / \u65b0\u52a0\u5761'],
    ['Asia/Tokyo', 'Tokyo / \u4e1c\u4eac'],
    ['Asia/Seoul', 'Seoul / \u9996\u5c14'],
    ['Australia/Sydney', 'Sydney / \u6089\u5c3c'],
    ['Europe/London', 'London / \u4f26\u6566'],
    ['Europe/Paris', 'Paris / \u5df4\u9ece'],
    ['America/New_York', 'New York / \u7ebd\u7ea6'],
    ['America/Los_Angeles', 'Los Angeles / \u6d1b\u6749\u77f6'],
    ['America/Toronto', 'Toronto / \u591a\u4f26\u591a']
  ];  const i18n = {
    en: {
      title: 'Overseas Review Platform', readonly: 'ReadOnly Mode Enabled', weekly: 'Date Range', range7: 'Last 7 Days', range30: 'Last 30 Days', export: 'Export', settings: 'Settings', help: 'Help Center', clock: 'Beijing Time', language: 'EN', timezone: 'Timezone', profile: 'Account', notifications: 'Notifications', taskOpened: 'New task panel opened. Review read-only scope before deployment.', exportDone: 'Export generated from current page state.', filterApplied: 'Filter action applied', langChanged: 'Language switched to English.', tzChanged: 'Timezone switched. Time is converted from Beijing reference time.', settingsTitle: 'Console Settings', settingsBody: 'Timezone and language are shared by all pages. Time is converted from Beijing time and updates every second.'
    },
    zh: {
      title: '\u6d77\u5916\u8bc4\u8bba\u91c7\u96c6\u5e73\u53f0', readonly: '\u53ea\u8bfb\u6a21\u5f0f\u5df2\u542f\u7528', weekly: '\u65e5\u671f\u8303\u56f4', range7: '\u8fd1 7 \u5929', range30: '\u8fd1 30 \u5929', export: '\u5bfc\u51fa', settings: '\u8bbe\u7f6e', help: '\u5e2e\u52a9\u4e2d\u5fc3', clock: '\u5317\u4eac\u65f6\u95f4', language: '\u4e2d\u6587', timezone: '\u65f6\u533a', profile: '\u8d26\u53f7', notifications: '\u901a\u77e5', taskOpened: '\u5df2\u6253\u5f00\u65b0\u4efb\u52a1\u9762\u677f\uff0c\u6267\u884c\u524d\u8bf7\u786e\u8ba4\u53ea\u8bfb\u8303\u56f4\u3002', exportDone: '\u5df2\u6839\u636e\u5f53\u524d\u9875\u9762\u72b6\u6001\u751f\u6210\u5bfc\u51fa\u6587\u4ef6\u3002', filterApplied: '\u7b5b\u9009\u52a8\u4f5c\u5df2\u5e94\u7528', langChanged: '\u8bed\u8a00\u5df2\u5207\u6362\u4e3a\u4e2d\u6587\u3002', tzChanged: '\u65f6\u533a\u5df2\u5207\u6362\uff0c\u65f6\u95f4\u4f9d\u636e\u5317\u4eac\u65f6\u95f4\u6362\u7b97\u5e76\u6bcf\u79d2\u66f4\u65b0\u3002', settingsTitle: '\u63a7\u5236\u53f0\u8bbe\u7f6e', settingsBody: '\u65f6\u533a\u548c\u8bed\u8a00\u8bbe\u7f6e\u5728\u6240\u6709\u9875\u9762\u5171\u4eab\u3002\u65f6\u95f4\u4ee5\u5317\u4eac\u65f6\u95f4\u4e3a\u57fa\u51c6\u6362\u7b97\uff0c\u5e76\u6bcf\u79d2\u81ea\u52a8\u66f4\u65b0\u3002'
    }
  };
  const textZh = {
    'Overseas Review': '\u6d77\u5916\u8bc4\u8bba',
    'Overseas Review Platform': '\u6d77\u5916\u8bc4\u8bba\u91c7\u96c6\u5e73\u53f0',
    'ReadOnly Mode Enabled': '\u53ea\u8bfb\u6a21\u5f0f\u5df2\u542f\u7528',
    'Export Report': '\u5bfc\u51fa\u62a5\u544a',
    'Settings': '\u8bbe\u7f6e', 'Help Center': '\u5e2e\u52a9\u4e2d\u5fc3', 'Weekly Range': '\u8fd1\u4e00\u5468\u8303\u56f4', 'Export': '\u5bfc\u51fa',
    'Dashboard': '\u4eea\u8868\u76d8', 'Collection Tasks': '\u91c7\u96c6\u4efb\u52a1', 'Store Coverage': '\u95e8\u5e97\u8986\u76d6', 'Review Workbench': '\u8bc4\u8bba\u5de5\u4f5c\u53f0', 'Platform Matrix': '\u5e73\u53f0\u77e9\u9635', 'Quality Report': '\u8d28\u91cf\u62a5\u544a', 'Safety & Audit': '\u5b89\u5168\u5ba1\u8ba1',
    'Manage and monitor automated review extraction processes.': '\u7ba1\u7406\u5e76\u76d1\u63a7\u81ea\u52a8\u5316\u8bc4\u8bba\u91c7\u96c6\u6d41\u7a0b\u3002',
    'Create New Task': '\u521b\u5efa\u65b0\u4efb\u52a1', 'Active Tasks': '\u6d3b\u52a8\u4efb\u52a1', 'Reviews Extracted (24h)': '24\u5c0f\u65f6\u5df2\u91c7\u96c6\u8bc4\u8bba', 'Failed Runs': '\u5931\u8d25\u8fd0\u884c', 'Success Rate': '\u6210\u529f\u7387',
    'Platform/Geo': '\u5e73\u53f0/\u5730\u533a', 'Scope': '\u8303\u56f4', 'Mode': '\u6a21\u5f0f', 'Extracted': '\u5df2\u91c7\u96c6', 'Timing': '\u65f6\u95f4', 'Action': '\u64cd\u4f5c', 'Status': '\u72b6\u6001',
    'New Collection Task': '\u65b0\u5efa\u91c7\u96c6\u4efb\u52a1', '1. Target Definition': '1. \u76ee\u6807\u5b9a\u4e49', '2. Data Parameters': '2. \u6570\u636e\u53c2\u6570', '3. Execution': '3. \u6267\u884c',
    'Platform': '\u5e73\u53f0', 'Country': '\u56fd\u5bb6/\u5730\u533a', 'Country/Region': '\u56fd\u5bb6/\u5730\u533a', 'All Regions': '\u5168\u90e8\u5730\u533a', 'All Platforms': '\u5168\u90e8\u5e73\u53f0', 'United Kingdom': '\u82f1\u56fd', 'United States': '\u7f8e\u56fd', 'Singapore': '\u65b0\u52a0\u5761', 'Store Scope': '\u95e8\u5e97\u8303\u56f4', 'All Active Stores': '\u6240\u6709\u6d3b\u8dc3\u95e8\u5e97', 'By JDE Code List': '\u6309 JDE \u7f16\u7801\u5217\u8868', 'By Store Name': '\u6309\u95e8\u5e97\u540d\u79f0', 'By Direct URL': '\u6309\u76f4\u8fde URL',
    'Date Range': '\u65e5\u671f\u8303\u56f4', 'Last 7 Days': '\u8fd1 7 \u5929', 'Last 30 Days': '\u8fd1 30 \u5929', 'Collect Now': '\u7acb\u5373\u91c7\u96c6', 'Start Sync': '\u5f00\u59cb\u540c\u6b65', 'Stop Sync': '\u505c\u6b62\u540c\u6b65', 'Dry Run': '\u6f14\u7ec3\u8fd0\u884c', 'Custom': '\u81ea\u5b9a\u4e49', 'Field Extraction': '\u5b57\u6bb5\u63d0\u53d6', 'Rating (Required)': '\u8bc4\u5206\uff08\u5fc5\u9700\uff09', 'Comment Text (Required)': '\u8bc4\u8bba\u6587\u672c\uff08\u5fc5\u9700\uff09', 'Auto-Translation': '\u81ea\u52a8\u7ffb\u8bd1', 'Image URLs': '\u56fe\u7247 URL', 'Order ID (If available)': '\u8ba2\u5355 ID\uff08\u5982\u6709\uff09',
    'Read-Only Mode': '\u53ea\u8bfb\u6a21\u5f0f', 'Platform policy enforces read-only access for this account tier. Writes are disabled.': '\u5e73\u53f0\u7b56\u7565\u5bf9\u8be5\u8d26\u53f7\u5f3a\u5236\u53ea\u8bfb\u8bbf\u95ee\uff0c\u5199\u5165\u52a8\u4f5c\u5df2\u7981\u7528\u3002', 'Run Method': '\u8fd0\u884c\u65b9\u5f0f', 'Immediate': '\u7acb\u5373\u6267\u884c', 'Scheduled': '\u5b9a\u65f6\u6267\u884c', 'Dry Run (Estimate limits)': '\u6f14\u7ec3\u8fd0\u884c\uff08\u4f30\u7b97\u9650\u989d\uff09', 'Cancel': '\u53d6\u6d88', 'Deploy Task': '\u90e8\u7f72\u4efb\u52a1',
    'Last 7 Days (Live)': '\u8fd1 7 \u5929\uff08\u5b9e\u65f6\uff09', '7-Day Review Intelligence Overview': '7\u5929\u8bc4\u8bba\u667a\u80fd\u603b\u89c8', 'Volume': '\u8bc4\u8bba\u91cf', 'Risk Signal Index': '\u98ce\u9669\u4fe1\u53f7\u6307\u6570', 'Chart visualization area. Requires JS charting library.': '\u56fe\u8868\u53ef\u89c6\u5316\u533a\u57df\uff0c\u9700\u8981 JS \u56fe\u8868\u5e93\u3002', 'Platform Connection Status': '\u5e73\u53f0\u8fde\u63a5\u72b6\u6001', 'Coverage Matrix': '\u8986\u76d6\u77e9\u9635', 'Region': '\u533a\u57df', 'High-Risk Exceptions': '\u9ad8\u98ce\u9669\u5f02\u5e38', 'View All': '\u67e5\u770b\u5168\u90e8',
    'Configuration and health status of all data extraction targets.': '\u6240\u6709\u6570\u636e\u91c7\u96c6\u76ee\u6807\u7684\u914d\u7f6e\u548c\u5065\u5eb7\u72b6\u6001\u3002', 'Filter': '\u7b5b\u9009', 'New Platform': '\u65b0\u5e73\u53f0', 'Platform Name': '\u5e73\u53f0\u540d\u79f0', 'Executor Path': '\u6267\u884c\u5668\u8def\u5f84', 'Login Method': '\u767b\u5f55\u65b9\u5f0f', 'Default Strategy': '\u9ed8\u8ba4\u7b56\u7565', 'Order': '\u8ba2\u5355', 'Img': '\u56fe\u7247', 'Trans': '\u7ffb\u8bd1', 'Human-Gate': '\u4eba\u5de5\u95e8', 'Actions': '\u64cd\u4f5c',
    'Constraints & Capabilities': '\u7ea6\u675f\u4e0e\u80fd\u529b', 'Safety Constraints': '\u5b89\u5168\u7ea6\u675f', 'STRICT: NO REPLY': '\u4e25\u683c\uff1a\u7981\u6b62\u56de\u590d', 'STRICT: NO DELETE': '\u4e25\u683c\uff1a\u7981\u6b62\u5220\u9664', 'STRICT: NO SUBMIT': '\u4e25\u683c\uff1a\u7981\u6b62\u63d0\u4ea4', 'Supported': '\u5df2\u652f\u6301', 'Unsupported': '\u672a\u652f\u6301', 'Recent Failures': '\u6700\u8fd1\u5931\u8d25', 'View all logs': '\u67e5\u770b\u6240\u6709\u65e5\u5fd7', 'Next Plan / Roadmap': '\u4e0b\u4e00\u6b65\u8ba1\u5212 / \u8def\u7ebf\u56fe', 'Known Issues': '\u5df2\u77e5\u95ee\u9898',
    'Data Quality Control': '\u6570\u636e\u8d28\u91cf\u63a7\u5236', 'System-wide monitoring of extraction fidelity and data integrity.': '\u5168\u7cfb\u7edf\u76d1\u63a7\u91c7\u96c6\u4fdd\u771f\u5ea6\u548c\u6570\u636e\u5b8c\u6574\u6027\u3002', 'Last Updated': '\u6700\u540e\u66f4\u65b0', 'Store': '\u95e8\u5e97', 'Rating': '\u8bc4\u5206', 'Sentiment': '\u60c5\u611f', 'Negative': '\u8d1f\u9762', 'Positive': '\u6b63\u9762', 'Partial': '\u90e8\u5206', 'Failed': '\u5931\u8d25', 'Pending': '\u7b49\u5f85', 'Running': '\u8fd0\u884c\u4e2d', 'Queued': '\u6392\u961f\u4e2d', 'Active': '\u6d3b\u8dc3', 'Covered': '\u5df2\u8986\u76d6', 'Success': '\u6210\u529f', 'Normal': '\u6b63\u5e38', 'No': '\u5426', 'All': '\u5168\u90e8', 'Today': '\u4eca\u65e5', 'Yesterday': '\u6628\u65e5', 'Reviews': '\u8bc4\u8bba', 'Photos': '\u56fe\u7247', 'Translation': '\u7ffb\u8bd1', 'Order Details': '\u8ba2\u5355\u8be6\u60c5', 'Data Capabilities': '\u6570\u636e\u80fd\u529b', 'Platform Entry': '\u5e73\u53f0\u5165\u53e3', 'Total Ingestion': '\u91c7\u96c6\u603b\u91cf', 'Avg Rating': '\u5e73\u5747\u8bc4\u5206', 'Sync Error': '\u540c\u6b65\u9519\u8bef', 'Pending Setup': '\u5f85\u914d\u7f6e', 'Search ID': '\u641c\u7d22 JDE', 'Search by name': '\u6309\u95e8\u5e97\u540d\u641c\u7d22', 'Showing': '\u663e\u793a', 'Stores': '\u5bb6\u95e8\u5e97',
    'Review Details': '\u8bc4\u8bba\u8be6\u60c5', 'Full Text Expanded': '\u5168\u6587\u5df2\u5c55\u5f00', 'Translation Fetched': '\u8bd1\u6587\u5df2\u83b7\u53d6', 'Content Analysis': '\u5185\u5bb9\u5206\u6790', 'Original Text': '\u539f\u6587', 'Original': '\u539f\u6587', 'Chinese Translation': '\u4e2d\u6587\u8bd1\u6587', 'Evidence Images': '\u8bc1\u636e\u56fe\u7247', 'Associated Order': '\u5173\u8054\u8ba2\u5355', 'Raw API Payload': '\u539f\u59cb API \u8f7d\u8377', 'Export Record': '\u5bfc\u51fa\u672c\u6761\u8bb0\u5f55', 'Customer': '\u7528\u6237', 'Review Time': '\u8bc4\u4ef7\u65f6\u95f4', 'Source File': '\u6765\u6e90\u6587\u4ef6', 'No real review records found': '\u672a\u627e\u5230\u771f\u5b9e\u91c7\u96c6\u8bc4\u8bba\u8bb0\u5f55', 'Run a collector or widen the date range to 30 days.': '\u8bf7\u5148\u8fd0\u884c\u91c7\u96c6\uff0c\u6216\u5c06\u65f6\u95f4\u8303\u56f4\u653e\u5bbd\u5230 30 \u5929\u3002', 'Real exports only': '\u4ec5\u663e\u793a\u771f\u5b9e\u5bfc\u51fa\u6570\u636e', 'Has Image': '\u6709\u56fe\u7247', 'Has Order': '\u6709\u8ba2\u5355', 'Language': '\u8bed\u8a00', 'Food Safety Keywords': '\u98df\u54c1\u5b89\u5168\u5173\u952e\u8bcd', 'Item': '\u5546\u54c1', 'Specs': '\u89c4\u683c', 'Qty': '\u6570\u91cf', 'Price': '\u4ef7\u683c', 'Order Total': '\u8ba2\u5355\u603b\u989d', 'Subtotal': '\u5c0f\u8ba1',
    'Safety & Audit Operations': '\u5b89\u5168\u4e0e\u5ba1\u8ba1\u64cd\u4f5c', 'Comprehensive monitoring and immutable logging of system activity, ensuring adherence to read-only compliance constraints.': '\u5168\u9762\u76d1\u63a7\u5e76\u4e0d\u53ef\u53d8\u8bb0\u5f55\u7cfb\u7edf\u6d3b\u52a8\uff0c\u786e\u4fdd\u7b26\u5408\u53ea\u8bfb\u5408\u89c4\u7ea6\u675f\u3002',
    'CREATE NEW TASK': '\u521b\u5efa\u65b0\u4efb\u52a1', 'EXPORT REPORT': '\u5bfc\u51fa\u62a5\u544a', 'WEEKLY RANGE': '\u8fd1\u4e00\u5468\u8303\u56f4', 'DEPLOY TASK': '\u90e8\u7f72\u4efb\u52a1', 'CANCEL': '\u53d6\u6d88',
    'ACTIVE TASKS': '\u6d3b\u52a8\u4efb\u52a1', 'REVIEWS': '\u8bc4\u8bba', 'FAILED RUNS': '\u5931\u8d25\u8fd0\u884c', 'SUCCESS RATE': '\u6210\u529f\u7387', 'TARGET DEFINITION': '\u76ee\u6807\u5b9a\u4e49', 'DATA PARAMETERS': '\u6570\u636e\u53c2\u6570', 'EXECUTION': '\u6267\u884c',
    'PLATFORM': '\u5e73\u53f0', 'COUNTRY': '\u56fd\u5bb6/\u5730\u533a', 'STATUS': '\u72b6\u6001', 'STORE NAME': '\u95e8\u5e97\u540d\u79f0', 'DATA CAPABILITIES': '\u6570\u636e\u80fd\u529b', 'PLATFORM ENTRY': '\u5e73\u53f0\u5165\u53e3', 'PLATFORMS': '\u5e73\u53f0', 'LOCATION': '\u4f4d\u7f6e', 'LAST SYNC': '\u6700\u540e\u540c\u6b65',
    '7-DAY REVIEW SUMMARY': '7 \u5929\u8bc4\u8bba\u6458\u8981', 'LIVE': '\u5b9e\u65f6', 'VERIFIED': '\u5df2\u9a8c\u8bc1', 'RESOLVED': '\u5df2\u89e3\u51b3', 'ABORTED': '\u5df2\u4e2d\u6b62', 'AUTO-SYNC ON': '\u81ea\u52a8\u540c\u6b65\u5df2\u5f00\u542f', 'BLOCKED_POLICY': '\u7b56\u7565\u963b\u6b62',
    'Weekly Reviews': '\u672c\u5468\u8bc4\u8bba\u6570', 'Negative Reviews': '\u98ce\u9669\u8bc4\u8bba\u6570', 'Low-Rating Orders': '\u4f4e\u8bc4\u5206\u8ba2\u5355', 'Reviews With Images': '\u6709\u56fe\u8bc4\u8bba', 'Translated Reviews': '\u5df2\u7ffb\u8bd1\u8bc4\u8bba', 'Failed Stores': '\u5931\u8d25\u95e8\u5e97',
    'READ_OK': '\u8bfb\u53d6\u6b63\u5e38', 'NAV_OK': '\u5bfc\u822a\u6b63\u5e38', 'FORBIDDEN': '\u5df2\u7981\u6b62', 'POSITIVE (85%)': '\u6b63\u9762\uff0885%\uff09', 'NEGATIVE (5%)': '\u8d1f\u9762\uff085%\uff09', 'MIXED (10%)': '\u6df7\u5408\uff0810%\uff09',
    'Read-Only Collection Policy (Inviolable)': '\u53ea\u8bfb\u91c7\u96c6\u7b56\u7565\uff08\u4e0d\u53ef\u8fdd\u53cd\uff09',
    'This system is structurally constrained to non-destructive operations. All automated and manual interactions are strictly limited to data retrieval. Any attempt to execute write, modify, or delete operations via automated scripts or API endpoints will be blocked at the network perimeter.': '\u672c\u7cfb\u7edf\u5728\u67b6\u6784\u4e0a\u53d7\u5236\u4e8e\u975e\u7834\u574f\u6027\u64cd\u4f5c\u3002\u6240\u6709\u81ea\u52a8\u548c\u4eba\u5de5\u4ea4\u4e92\u5747\u4e25\u683c\u9650\u5b9a\u4e3a\u6570\u636e\u8bfb\u53d6\u3002\u4efb\u4f55\u901a\u8fc7\u81ea\u52a8\u5316\u811a\u672c\u6216 API \u7aef\u70b9\u6267\u884c\u5199\u5165\u3001\u4fee\u6539\u6216\u5220\u9664\u7684\u5c1d\u8bd5\uff0c\u90fd\u4f1a\u5728\u7f51\u7edc\u8fb9\u754c\u88ab\u963b\u65ad\u3002',
    'Task Audit Log (Browser Automation)': '\u4efb\u52a1\u5ba1\u8ba1\u65e5\u5fd7\uff08\u6d4f\u89c8\u5668\u81ea\u52a8\u5316\uff09',
    'Human-Gate Records': '\u4eba\u5de5\u4ecb\u5165\u8bb0\u5f55',
    'CAPTCHA Challenge': '\u9a8c\u8bc1\u7801\u6311\u6218',
    'Write-Action Suspected': '\u7591\u4f3c\u5199\u5165\u64cd\u4f5c',
    'Form submission field detected in viewport during automated scroll. Task terminated as safety precaution.': '\u81ea\u52a8\u6eda\u52a8\u671f\u95f4\u68c0\u6d4b\u5230\u89c6\u53e3\u5185\u5b58\u5728\u8868\u5355\u63d0\u4ea4\u5b57\u6bb5\u3002\u4e3a\u5b89\u5168\u8d77\u89c1\uff0c\u4efb\u52a1\u5df2\u7ec8\u6b62\u3002',
    'Unusual Login Pattern': '\u5f02\u5e38\u767b\u5f55\u6a21\u5f0f',
    'Merchant session token refresh required manual re-authentication.': '\u5546\u5bb6\u540e\u53f0\u4f1a\u8bdd\u4ee4\u724c\u5237\u65b0\u9700\u8981\u4eba\u5de5\u91cd\u65b0\u8ba4\u8bc1\u3002',
    'Export Activity Log': '\u5bfc\u51fa\u6d3b\u52a8\u65e5\u5fd7',
    'Google Maps POI scraping interrupted. Manual solver initiated by operator.': 'Google Maps POI \u91c7\u96c6\u88ab\u4e2d\u65ad\uff0c\u5df2\u7531\u64cd\u4f5c\u5458\u542f\u52a8\u4eba\u5de5\u89e3\u9898\u3002',
    'System Auto-Job': '\u7cfb\u7edf\u81ea\u52a8\u4efb\u52a1',
    'Timestamp': '\u65f6\u95f4\u6233',
    'Task ID': '\u4efb\u52a1 ID',
    'Target Node': '\u76ee\u6807\u8282\u70b9',
    'Action Type': '\u64cd\u4f5c\u7c7b\u578b',
    'Operation Type': '\u64cd\u4f5c\u7c7b\u578b',
    'Platform event': '\u5e73\u53f0\u4e8b\u4ef6',
    'Human-gate event': '\u4eba\u5de5\u95e8\u4e8b\u4ef6',
    'No audit events yet': '\u6682\u65e0\u5ba1\u8ba1\u4e8b\u4ef6',
    'No human-gate events': '\u6682\u65e0\u4eba\u5de5\u95e8\u4e8b\u4ef6',
    'System Export Job': '\u7cfb\u7edf\u5bfc\u51fa\u4efb\u52a1',
    'No export records': '\u6682\u65e0\u5bfc\u51fa\u8bb0\u5f55',
    'info': '\u4fe1\u606f',
    'success': '\u6210\u529f',
    'warning': '\u8b66\u544a',
    'error': '\u9519\u8bef',
    'Sync monitor stopped': '\u540c\u6b65\u76d1\u63a7\u5df2\u505c\u6b62',
    'Background platform synchronization has been stopped.': '\u540e\u53f0\u5e73\u53f0\u540c\u6b65\u5df2\u505c\u6b62\u3002',
    'Platform sync dry-run completed': '\u5e73\u53f0\u540c\u6b65\u6f14\u7ec3\u5df2\u5b8c\u6210',
    'Sync monitor started': '\u540c\u6b65\u76d1\u63a7\u5df2\u542f\u52a8',
    'Settings saved': '\u8bbe\u7f6e\u5df2\u4fdd\u5b58',
    'Runtime collection settings were updated.': '\u8fd0\u884c\u65f6\u91c7\u96c6\u8bbe\u7f6e\u5df2\u66f4\u65b0\u3002',
    'Sync interval updated': '\u540c\u6b65\u95f4\u9694\u5df2\u66f4\u65b0',
    'Background sync interval set to': '\u540e\u53f0\u540c\u6b65\u95f4\u9694\u8bbe\u7f6e\u4e3a',
    'task template(s), interval': '\u4e2a\u4efb\u52a1\u6a21\u677f\uff0c\u95f4\u9694',
    'Reply': '\u56de\u590d',
    'Save': '\u4fdd\u5b58',
    'Submit': '\u63d0\u4ea4',
    'Delete': '\u5220\u9664',
    'Confirm': '\u786e\u8ba4',
    'Payment': '\u652f\u4ed8'
  };
  const textEn = Object.fromEntries(Object.entries(textZh).map(([en, zh]) => [zh, en]));
  const textZhLower = Object.fromEntries(Object.entries(textZh).map(([en, zh]) => [en.toLowerCase(), zh]));
  const textEnLower = Object.fromEntries(Object.entries(textEn).map(([zh, en]) => [zh.toLowerCase(), en]));
  const i18nKeys = {
    brand_name: { en: 'HEYTEA', zh: '喜茶' },
    app_subtitle: { en: 'Overseas Review', zh: '海外评论' },
    nav_dashboard: { en: 'Dashboard', zh: '仪表盘' },
    nav_collection_tasks: { en: 'Collection Tasks', zh: '采集任务' },
    nav_store_coverage: { en: 'Store Coverage', zh: '门店覆盖' },
    nav_review_workbench: { en: 'Review Workbench', zh: '评论工作台' },
    nav_platform_matrix: { en: 'Platform Matrix', zh: '平台矩阵' },
    nav_quality_report: { en: 'Quality Report', zh: '质量报告' },
    nav_safety_audit: { en: 'Safety & Audit', zh: '安全与审计' },
    nav_settings: { en: 'Settings', zh: '设置' },
    nav_help_center: { en: 'Help Center', zh: '帮助中心' },
    header_title: { en: 'Overseas Review Platform', zh: '海外评论采集平台' },
    header_date_range: { en: 'Last 7 Days (Live)', zh: '近 7 天（实时）' },
    status_readonly: { en: 'ReadOnly Mode Enabled', zh: '只读模式已启用' },
    action_export_report: { en: 'Export Report', zh: '导出报告' },
    action_weekly_range: { en: 'Weekly Range', zh: '近一周范围' },
    action_export: { en: 'Export', zh: '导出' },
    action_view_all: { en: 'View All', zh: '查看全部' },
    metric_weekly_reviews: { en: 'Weekly Reviews', zh: '本周评论数' },
    metric_negative_reviews: { en: 'High-Risk Reviews', zh: '风险评论数' },
    metric_low_rating_orders: { en: 'Low-Rating Orders', zh: '低评分订单' },
    metric_reviews_with_images: { en: 'Reviews With Images', zh: '有图评论' },
    metric_translated_reviews: { en: 'Translated Reviews', zh: '已翻译评论' },
    metric_failed_stores: { en: 'Failed Stores', zh: '失败门店' },
    chart_title_volume_vs_negative: { en: '7-Day Review Intelligence Overview', zh: '7天评论智能总览' },
    chart_legend_volume: { en: 'Volume', zh: '评论量' },
    chart_legend_negative_rate: { en: 'Risk Trend Index', zh: '风险趋势指数' },
    chart_placeholder_text: { en: 'Chart visualization area. Requires JS charting library.', zh: '图表可视化区域，需要 JS 图表库。' },
    platform_status_title: { en: 'Platform Connection Status', zh: '平台连接状态' },
    platform_google_maps: { en: 'Google Maps', zh: 'Google Maps' },
    platform_hungry_panda: { en: 'Hungry Panda', zh: 'Hungry Panda' },
    platform_fantuan: { en: 'Fantuan', zh: '饭团' },
    platform_grabfood: { en: 'GrabFood', zh: 'GrabFood' },
    platform_keeta: { en: 'KeeTa', zh: 'KeeTa' },
    platform_openrice: { en: 'OpenRice', zh: 'OpenRice 开饭喇' },
    platform_mfood: { en: 'Mfood', zh: 'Mfood' },
    status_success: { en: 'Success', zh: '成功' },
    status_failed: { en: 'Failed', zh: '失败' },
    status_pending: { en: 'Pending', zh: '等待' },
    status_partial: { en: 'Partial', zh: '部分完成' },
    matrix_title: { en: 'Coverage Matrix', zh: '覆盖矩阵' },
    matrix_col_region: { en: 'Region', zh: '区域' },
    matrix_col_google: { en: 'Google', zh: 'Google' },
    matrix_col_grab: { en: 'Grab', zh: 'Grab' },
    matrix_col_panda: { en: 'Panda', zh: 'Panda' },
    region_singapore: { en: 'Singapore', zh: '新加坡' },
    region_malaysia: { en: 'Malaysia', zh: '马来西亚' },
    region_uk: { en: 'UK', zh: '英国' },
    region_usa: { en: 'USA', zh: '美国' },
    legend_active: { en: 'Active', zh: '活跃' },
    legend_failed: { en: 'Failed', zh: '失败' },
    legend_partial: { en: 'Partial', zh: '部分完成' },
    legend_pending_na: { en: 'Pending/N/A', zh: '等待/不适用' },
    exceptions_title: { en: 'High-Risk Exceptions', zh: '高风险异常' },
    review_store_sg_orchard: { en: 'SG-Orchard', zh: '新加坡 Orchard' },
    review_store_uk_soho: { en: 'UK-Soho', zh: '英国 Soho' },
    review_store_my_klcc: { en: 'MY-KLCC', zh: '马来西亚 KLCC' },
    review_platform_google_maps: { en: 'Google Maps', zh: 'Google Maps' },
    review_platform_hungry_panda: { en: 'HungryPanda', zh: 'HungryPanda' },
    review_platform_grabfood: { en: 'GrabFood', zh: 'GrabFood' },
    review_text_1: {
      en: '"Found a hair in my drink, completely unacceptable. Tried to call the store but no one answered."',
      zh: '“饮品里发现头发，完全不能接受。尝试联系门店，但无人接听。”'
    },
    review_text_2: {
      en: '"Delivery took over 2 hours. Drink was warm when it arrived. Taste is okay but very disappointed with speed."',
      zh: '“配送超过 2 小时，饮品送达时已经变温。口味还可以，但配送速度令人失望。”'
    },
    review_text_3: {
      en: '"Staff was incredibly rude when I asked about my order status. Cup lid was loose and spilled everywhere."',
      zh: '“询问订单状态时员工态度非常差。杯盖松动，饮品洒得到处都是。”'
    },
    tag_hygiene: { en: 'Hygiene', zh: '卫生' },
    tag_service: { en: 'Service', zh: '服务' },
    tag_delivery_time: { en: 'Delivery Time', zh: '配送时效' },
    tag_attitude: { en: 'Attitude', zh: '态度' },
    tag_packaging: { en: 'Packaging', zh: '包装' }
  };
  const escapeRegExp = s => String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  function lookupText(map, lowerMap, text) {
    return map[text] || lowerMap[text.toLowerCase()] || null;
  }
  function replacePhrases(text, map) {
    let output = String(text || '');
    const phrases = Object.keys(map).sort((a, b) => b.length - a.length);
    for (const phrase of phrases) {
      if (!phrase || phrase.length < 3) continue;
      const escaped = escapeRegExp(phrase);
      const isAsciiPhrase = /^[\x20-\x7E]+$/.test(phrase) && /[A-Za-z]/.test(phrase);
      if (isAsciiPhrase) {
        const re = new RegExp(`(^|[^A-Za-z0-9])(${escaped})(?=$|[^A-Za-z0-9])`, 'gi');
        output = output.replace(re, (_m, lead) => `${lead}${map[phrase]}`);
      } else {
        const re = new RegExp(escaped, 'gi');
        output = output.replace(re, map[phrase]);
      }
    }
    return output;
  }

  const cleanText = el => (el && (el.innerText || el.textContent) || '').replace(/\s+/g, ' ').trim();
  const lang = () => localStorage.getItem('heytea_lang') || 'en';
  const t = key => (i18n[lang()] || i18n.en)[key] || i18n.en[key] || key;
  const tz = () => localStorage.getItem('heytea_timezone') || 'Asia/Shanghai';
  const formatLocalDateToken = date => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  const tokenToLocalDate = token => {
    const match = String(token || '').match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (!match) return null;
    const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
    date.setHours(0, 0, 0, 0);
    return Number.isNaN(date.getTime()) ? null : date;
  };
  const beijingTodayToken = () => {
    const formatter = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Asia/Shanghai',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
    const parts = Object.fromEntries(formatter.formatToParts(new Date()).filter(p => p.type !== 'literal').map(p => [p.type, p.value]));
    return `${parts.year}-${parts.month}-${parts.day}`;
  };
  const isoDateToken = value => {
    const date = value instanceof Date ? new Date(value) : new Date(value);
    if (Number.isNaN(date.getTime())) return '';
    date.setHours(0, 0, 0, 0);
    return formatLocalDateToken(date);
  };
  const defaultDashboardRange = (days = 7) => {
    const safeDays = Math.max(1, Math.min(30, Number(days || 7)));
    const end = tokenToLocalDate(beijingTodayToken()) || new Date();
    const start = new Date(end);
    start.setDate(end.getDate() - safeDays + 1);
    return { start: isoDateToken(start), end: isoDateToken(end), span: safeDays };
  };
  const dashboardRangeState = (days = 7) => {
    const fallback = defaultDashboardRange(days);
    const mode = String(localStorage.getItem('heytea_dashboard_range_mode') || '').trim();
    if (mode !== 'custom') {
      return fallback;
    }
    let start = String(localStorage.getItem('heytea_dashboard_range_start') || '').trim();
    let end = String(localStorage.getItem('heytea_dashboard_range_end') || '').trim();
    if (!/^\d{4}-\d{2}-\d{2}$/.test(start) || !/^\d{4}-\d{2}-\d{2}$/.test(end)) return fallback;
    const startDate = new Date(`${start}T00:00:00`);
    const endDate = new Date(`${end}T00:00:00`);
    if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) return fallback;
    let safeStart = startDate;
    let safeEnd = endDate;
    const today = tokenToLocalDate(beijingTodayToken()) || new Date();
    if (safeStart > safeEnd) [safeStart, safeEnd] = [safeEnd, safeStart];
    if (safeEnd > today) safeEnd = today;
    const oldestAllowedEnd = new Date(today);
    oldestAllowedEnd.setDate(today.getDate() - 29);
    if (safeEnd < oldestAllowedEnd) {
      localStorage.setItem('heytea_dashboard_range_mode', 'rolling');
      return fallback;
    }
    const span = Math.max(1, Math.floor((safeEnd.getTime() - safeStart.getTime()) / 86400000) + 1);
    if (span > 30) {
      safeStart = new Date(safeEnd);
      safeStart.setDate(safeEnd.getDate() - 29);
    }
    return {
      start: isoDateToken(safeStart),
      end: isoDateToken(safeEnd),
      span: Math.max(1, Math.floor((safeEnd.getTime() - safeStart.getTime()) / 86400000) + 1),
    };
  };
  const persistDashboardRange = (start, end, mode = 'custom') => {
    localStorage.setItem('heytea_dashboard_range_start', String(start || ''));
    localStorage.setItem('heytea_dashboard_range_end', String(end || ''));
    localStorage.setItem('heytea_dashboard_range_mode', mode === 'custom' ? 'custom' : 'rolling');
  };
  const selectedDays = () => {
    const days = parseInt(localStorage.getItem('heytea_days') || '7', 10);
    return days === 30 ? 30 : 7;
  };
  const selectedRangeLabel = () => selectedDays() === 30 ? t('range30') : t('range7');
  const regionPolicies = {
    zh: [
      [/中国香港特别行政区|香港特别行政区|香港/g, '中国香港'],
      [/中国澳门特别行政区|澳门特别行政区|澳門特別行政區|澳门|澳門/g, '中国澳门'],
      [/中国台湾省|台灣地區|台湾地区|台灣|台湾/g, '中国台湾'],
      [/\bHong[\s_-]*Kong\b/gi, '中国香港'],
      [/\bMacau\b/gi, '中国澳门'],
      [/\bMacao\b/gi, '中国澳门'],
      [/\bTaiwan\b/gi, '中国台湾'],
      [/\bHK\b/g, '中国香港'],
      [/\bMO\b/g, '中国澳门'],
      [/\bTW\b/g, '中国台湾'],
    ],
    en: [
      [/中国香港特别行政区|香港特别行政区|香港/g, 'China Hong Kong'],
      [/中国澳门特别行政区|澳门特别行政区|澳門特別行政區|澳门|澳門/g, 'China Macau'],
      [/中国台湾省|台灣地區|台湾地区|台灣|台湾/g, 'China Taiwan'],
      [/\bHong\s*Kong\b/gi, 'China Hong Kong'],
      [/\bMacau\b/gi, 'China Macau'],
      [/\bMacao\b/gi, 'China Macau'],
      [/\bTaiwan\b/gi, 'China Taiwan'],
      [/\bHK\b/g, 'China Hong Kong'],
      [/\bMO\b/g, 'China Macau'],
      [/\bTW\b/g, 'China Taiwan'],
    ],
  };
  const normalizeRegionText = value => {
    const source = String(value ?? '');
    const mode = lang() === 'zh' ? 'zh' : 'en';
    let output = source;
    for (const [pattern, replacement] of regionPolicies[mode]) output = output.replace(pattern, replacement);
    output = output
      .replace(/(中国)+香港/g, '中国香港')
      .replace(/(中国)+澳门/g, '中国澳门')
      .replace(/(中国)+台湾/g, '中国台湾')
      .replace(/(China\s+)+Hong Kong/gi, 'China Hong Kong')
      .replace(/(China\s+)+Macau/gi, 'China Macau')
      .replace(/(China\s+)+Taiwan/gi, 'China Taiwan');
    return output.replace(/\s+/g, ' ').trim();
  };
  const normalizeRegionForMatrix = value => {
    let output = String(value ?? '');
    output = output
      .replace(/香港特别行政区|香港/g, '中国香港')
      .replace(/澳门特别行政区|澳門特別行政區|澳门|澳門/g, '中国澳门')
      .replace(/台湾地区|台灣地區|台湾|台灣/g, '中国台湾')
      .replace(/\bHong\s*Kong\b/gi, '中国香港')
      .replace(/\bMacau\b/gi, '中国澳门')
      .replace(/\bMacao\b/gi, '中国澳门')
      .replace(/\bTaiwan\b/gi, '中国台湾')
      .replace(/(中国)+香港/g, '中国香港')
      .replace(/(中国)+澳门/g, '中国澳门')
      .replace(/(中国)+台湾/g, '中国台湾');
    return output.replace(/\s+/g, ' ').trim();
  };
  const normalizeLegacyYearText = value => {
    const source = String(value ?? '');
    if (!source) return source;
    const nowStamp = formatIsoInZone(new Date().toISOString());
    return source
      .replace(/20(23|24)[-/.]\d{2}[-/.]\d{2}(?:\s+\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?)?(?:\s*(?:UTC|Z))?/g, nowStamp)
      .replace(/20(23|24)\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日(?:\s*\d{1,2}:\d{1,2}(?::\d{1,2})?)?/g, nowStamp);
  };
  const notificationState = () => {
    try {
      return JSON.parse(localStorage.getItem('heytea_notifications') || '{"unseen":0,"events":[]}');
    } catch (_error) {
      return { unseen: 0, events: [] };
    }
  };
  const saveNotificationState = state => {
    const safe = {
      unseen: Math.max(0, Number(state?.unseen || 0)),
      events: Array.isArray(state?.events) ? state.events.slice(0, 80) : [],
    };
    localStorage.setItem('heytea_notifications', JSON.stringify(safe));
    const badge = document.getElementById('heytea-notify-badge');
    if (badge) {
      if (safe.unseen > 0) {
        badge.textContent = safe.unseen > 99 ? '99+' : String(safe.unseen);
        badge.hidden = false;
      } else {
        badge.textContent = '';
        badge.hidden = true;
      }
    }
  };
  const getZonedParts = (date, zone) => {
    const formatter = new Intl.DateTimeFormat('en-CA', {
      timeZone: zone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
    return Object.fromEntries(formatter.formatToParts(date).filter(p => p.type !== 'literal').map(p => [p.type, p.value]));
  };
  const BEIJING_ZONE = 'Asia/Shanghai';
  const toInt = value => Number.parseInt(value, 10) || 0;
  const zoneOffsetMinutes = (date, zone) => {
    const parts = getZonedParts(date, zone);
    const asUtc = Date.UTC(toInt(parts.year), toInt(parts.month) - 1, toInt(parts.day), toInt(parts.hour), toInt(parts.minute), toInt(parts.second));
    return Math.round((asUtc - date.getTime()) / 60000);
  };
  const formatUtcOffset = offsetMinutes => {
    const sign = offsetMinutes >= 0 ? '+' : '-';
    const absolute = Math.abs(offsetMinutes);
    const hours = String(Math.floor(absolute / 60)).padStart(2, '0');
    const minutes = String(absolute % 60).padStart(2, '0');
    return `UTC${sign}${hours}:${minutes}`;
  };
  const describeDeltaFromBeijing = (date, zone) => {
    const targetOffset = zoneOffsetMinutes(date, zone);
    const beijingOffset = zoneOffsetMinutes(date, BEIJING_ZONE);
    const delta = targetOffset - beijingOffset;
    if (delta === 0) return lang() === 'zh' ? '与北京时间一致' : 'Same as Beijing time';
    const abs = Math.abs(delta);
    const hours = Math.floor(abs / 60);
    const minutes = abs % 60;
    const hourText = minutes === 0 ? `${hours}` : `${hours}h ${minutes}m`;
    if (lang() === 'zh') {
      return delta < 0
        ? `较北京时间晚 ${minutes === 0 ? `${hours} 小时` : `${hours} 小时 ${minutes} 分钟`}`
        : `较北京时间早 ${minutes === 0 ? `${hours} 小时` : `${hours} 小时 ${minutes} 分钟`}`;
    }
    return delta < 0
      ? `${hourText} behind Beijing time`
      : `${hourText} ahead of Beijing time`;
  };
  const zonedDateString = (date, zone) => {
    const parts = getZonedParts(date, zone);
    return `${parts.year}-${parts.month}-${parts.day}`;
  };
  const liveRangeLabel = (days = selectedDays(), zone = tz()) => {
    const range = dashboardRangeState(days);
    if (lang() === 'zh') return `近 ${range.span} 天（${range.start} 至 ${range.end}）`;
    return `Last ${range.span} Days (${range.start} to ${range.end})`;
  };
  const updateDynamicDateLabels = () => {
    const days = selectedDays();
    const zone = tz();
    const label = normalizeComplianceText(liveRangeLabel(days, zone));
    document.querySelectorAll('[data-i18n="header_date_range"]').forEach(node => { node.textContent = label; });
    document.querySelectorAll('[data-heytea-days]').forEach(node => {
      node.textContent = selectedRangeLabel();
      node.dataset.heyteaDays = String(days);
    });
    const headerHint = document.querySelector('header [data-heytea-live-range]');
    if (headerHint) headerHint.textContent = label;
    document.querySelectorAll('header span, header div').forEach(node => {
      const text = cleanText(node);
      if (!text) return;
      if (/^(This Week|Last\s+\d+\s+Days)\s*\(20\d{2}-\d{2}-\d{2}\s+to\s+20\d{2}-\d{2}-\d{2}\)$/i.test(text)) {
        node.textContent = label;
      }
      if (/^(本周|近\s*\d+\s*天)[（(]20\d{2}-\d{2}-\d{2}\s*(至|to)\s*20\d{2}-\d{2}-\d{2}[）)]$/.test(text)) {
        node.textContent = label;
      }
    });
  };
  const setSelectedDays = days => {
    const safeDays = parseInt(days, 10) === 30 ? 30 : 7;
    localStorage.setItem('heytea_days', String(safeDays));
    const range = defaultDashboardRange(safeDays);
    persistDashboardRange(range.start, range.end, 'rolling');
    updateDynamicDateLabels();
    return safeDays;
  };
  const nextDashboardRenderSeq = () => {
    const seq = Number(window.__heyteaDashboardRenderSeq || 0) + 1;
    window.__heyteaDashboardRenderSeq = seq;
    return seq;
  };
  const isActiveDashboardRender = seq => (
    pageByPath() === 'dashboard'
    && Number(window.__heyteaDashboardRenderSeq || 0) === Number(seq)
  );
  const nextQualityRenderSeq = () => {
    const seq = Number(window.__heyteaQualityRenderSeq || 0) + 1;
    window.__heyteaQualityRenderSeq = seq;
    return seq;
  };
  const isActiveQualityRender = seq => (
    pageByPath() === 'quality_report'
    && Number(window.__heyteaQualityRenderSeq || 0) === Number(seq)
  );
  function pageByPath() {
    const path = location.pathname;
    const hit = routes.find(([key, en, zh, icon, href]) => path === href || path.endsWith(href.replace('/stitch-static/', '')));
    if (hit) return hit[0];
    if (path.endsWith('/index.html') || path === '/stitch-static/' || path === '/') return 'dashboard';
    return 'dashboard';
  }
  function notify(message) {
    let node = document.getElementById('heytea-toast');
    if (!node) { node = document.createElement('div'); node.id = 'heytea-toast'; node.className = 'heytea-toast'; document.body.appendChild(node); }
    node.textContent = message;
    clearTimeout(window.__heyteaToastTimer);
    window.__heyteaToastTimer = setTimeout(() => node.remove(), 2800);
  }
  function showLoginSplash() {
    if (sessionStorage.getItem('heytea_login_splash_seen')) return;
    sessionStorage.setItem('heytea_login_splash_seen', '1');
    const splash = document.createElement('div');
    splash.className = 'heytea-login-splash';
    splash.innerHTML = `<div class="heytea-login-card"><h1 class="heytea-login-title">HEYTEA</h1><p class="heytea-login-subtitle">${lang() === 'zh' ? '海外评论采集平台正在安全初始化' : 'Overseas review console is initializing safely'}</p><div class="heytea-login-loader"></div><div class="heytea-login-meta">${formatIsoInZone(new Date().toISOString())} · ${normalizeRegionText(tz())}</div></div>`;
    document.body.appendChild(splash);
    setTimeout(() => {
      splash.classList.add('fade-out');
      setTimeout(() => splash.remove(), 420);
    }, 1700);
  }
  function download(name, text, mime) {
    const blob = new Blob([text], { type: mime || 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }
  function showModal(title, body) {
    document.querySelectorAll('.heytea-modal-backdrop').forEach(x => x.remove());
    const backdrop = document.createElement('div');
    backdrop.className = 'heytea-modal-backdrop';
    backdrop.innerHTML = `<div class="heytea-modal"><header><span></span><button type="button">Close</button></header><section></section></div>`;
    backdrop.querySelector('header span').textContent = title;
    backdrop.querySelector('section').textContent = body;
    backdrop.querySelector('button').addEventListener('click', () => backdrop.remove());
    backdrop.addEventListener('click', e => { if (e.target === backdrop) backdrop.remove(); });
    document.body.appendChild(backdrop);
  }
  function showRangeModal() {
    document.querySelectorAll('.heytea-modal-backdrop').forEach(x => x.remove());
    const backdrop = document.createElement('div');
    backdrop.className = 'heytea-modal-backdrop';
    const currentDays = selectedDays();
    const title = lang() === 'zh' ? '\u91c7\u96c6\u65e5\u671f\u8303\u56f4' : 'Collection Date Range';
    const intro = lang() === 'zh'
      ? '\u6240\u6709\u5e73\u53f0\u540c\u6b65\u3001\u7acb\u5373\u91c7\u96c6\u548c\u6f14\u7ec3\u8fd0\u884c\u90fd\u4f7f\u7528\u8fd9\u4e2a\u8303\u56f4\u3002\u4e3a\u964d\u4f4e\u98ce\u9669\uff0c\u6700\u5927\u4fdd\u7559 30 \u5929\u3002'
      : 'All platform sync, collect-now and dry-run actions use this range. The maximum retained option is 30 days.';
    backdrop.innerHTML = `
      <div class="heytea-modal heytea-range-modal">
        <header><span>${title}</span><button type="button" data-close="true">Close</button></header>
        <section>
          <p>${intro}</p>
          <div class="heytea-range-options">
            <button type="button" data-days="7" class="${currentDays === 7 ? 'is-active' : ''}">${t('range7')}</button>
            <button type="button" data-days="30" class="${currentDays === 30 ? 'is-active' : ''}">${t('range30')}</button>
          </div>
          <div class="heytea-range-actions">
            <button type="button" data-range-action="dry-run">Dry Run</button>
            <button type="button" data-range-action="collect">Collect Now</button>
            <button type="button" data-range-action="start-sync">Start Sync</button>
            <button type="button" data-range-action="stop-sync">Stop Sync</button>
          </div>
          <pre class="heytea-range-output" aria-live="polite"></pre>
        </section>
      </div>`;
    const output = backdrop.querySelector('.heytea-range-output');
    const writeOutput = value => { output.textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2); };
    backdrop.querySelectorAll('[data-days]').forEach(button => button.addEventListener('click', () => {
      setSelectedDays(button.dataset.days);
      backdrop.querySelectorAll('[data-days]').forEach(peer => peer.classList.toggle('is-active', peer === button));
      notify(`${t('filterApplied')}: ${selectedRangeLabel()}`);
    }));
    backdrop.querySelectorAll('[data-range-action]').forEach(button => button.addEventListener('click', async () => {
      const action = button.dataset.rangeAction;
      const days = selectedDays();
      button.disabled = true;
      writeOutput(`${action}: ${days} days...`);
      try {
        let result;
        if (action === 'dry-run') result = await apiJson('/api/unified/dry-run', { method: 'POST', body: JSON.stringify({ platform: 'google_maps', days }) });
        if (action === 'collect') result = await apiJson('/api/unified/monitor/run-once', { method: 'POST', body: JSON.stringify({ days, dry_run: false }) });
        if (action === 'start-sync') {
          const intervalSeconds = await getSyncIntervalSeconds();
          result = await apiJson('/api/unified/monitor/start', { method: 'POST', body: JSON.stringify({ days, dry_run: false, interval_seconds: intervalSeconds }) });
        }
        if (action === 'stop-sync') result = await apiJson('/api/unified/monitor/stop', { method: 'POST', body: '{}' });
        writeOutput(result);
        notify(`${action}: ${days} days`);
      } catch (error) {
        writeOutput(String(error));
        notify(`Backend API error: ${error.message || error}`);
      } finally {
        button.disabled = false;
      }
    }));
    backdrop.querySelector('[data-close="true"]').addEventListener('click', () => backdrop.remove());
    backdrop.addEventListener('click', e => { if (e.target === backdrop) backdrop.remove(); });
    document.body.appendChild(backdrop);
  }
  async function showFolderPicker(settingPath) {
    document.querySelectorAll('.heytea-modal-backdrop').forEach(x => x.remove());
    const root = document.querySelector('.heytea-settings-shell');
    const targetInput = root?.querySelector(`[data-setting-path="${settingPath}"]`);
    if (!targetInput) {
      showModal('Folder Picker', `Setting input not found: ${settingPath}`);
      return;
    }
    const backdrop = document.createElement('div');
    backdrop.className = 'heytea-modal-backdrop';
    backdrop.innerHTML = `
      <div class="heytea-modal heytea-range-modal">
        <header><span>${lang() === 'zh' ? '选择文件夹' : 'Choose Folder'}</span><button type="button" data-close="true">${lang() === 'zh' ? '关闭' : 'Close'}</button></header>
        <section>
          <div class="heytea-folder-toolbar">
            <button type="button" data-folder-action="home">${lang() === 'zh' ? '工作区根目录' : 'Workspace Root'}</button>
            <button type="button" data-folder-action="up">${lang() === 'zh' ? '上一级' : 'Up'}</button>
            <button type="button" data-folder-action="choose" class="heytea-settings-primary">${lang() === 'zh' ? '使用当前目录' : 'Use Current Folder'}</button>
          </div>
          <div class="heytea-folder-current"></div>
          <div class="heytea-folder-list"></div>
          <pre class="heytea-range-output" aria-live="polite"></pre>
        </section>
      </div>`;
    const currentNode = backdrop.querySelector('.heytea-folder-current');
    const listNode = backdrop.querySelector('.heytea-folder-list');
    const outputNode = backdrop.querySelector('.heytea-range-output');
    let currentPath = String(targetInput.value || '').trim();
    let currentDisplay = currentPath;
    let parentPath = '';
    let workspaceRoot = '';
    const writeOutput = value => { outputNode.textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2); };
    const escapePath = value => encodeURIComponent(String(value || ''));
    const load = async (pathValue) => {
      const payload = await apiJson(`/api/unified/fs/dirs?path=${escapePath(pathValue || '')}&limit=500`);
      currentPath = payload.current || '';
      currentDisplay = payload.current_display || currentPath;
      parentPath = payload.parent || '';
      workspaceRoot = payload.workspace_root || '';
      currentNode.textContent = `${lang() === 'zh' ? '当前目录' : 'Current'}: ${currentDisplay || currentPath}`;
      listNode.innerHTML = (payload.dirs || []).length
        ? payload.dirs.map(item => `<button type="button" class="heytea-folder-item" data-folder-path="${escapeHtml(item.path || '')}" title="${escapeHtml(item.path || '')}">${escapeHtml(item.name || item.path || '-')}</button>`).join('')
        : `<div class="text-body-sm text-secondary">${escapeHtml(lang() === 'zh' ? '该目录无子文件夹' : 'No subfolders')}</div>`;
      listNode.querySelectorAll('[data-folder-path]').forEach(button => button.addEventListener('click', async () => {
        try {
          await load(button.dataset.folderPath || '');
        } catch (error) {
          writeOutput(String(error.message || error));
        }
      }));
      writeOutput({ current: currentDisplay || currentPath, count: payload.count || 0 });
    };
    backdrop.querySelectorAll('[data-folder-action]').forEach(button => button.addEventListener('click', async () => {
      const action = button.dataset.folderAction;
      if (action === 'choose') {
        targetInput.value = currentDisplay || currentPath;
        backdrop.remove();
        notify(lang() === 'zh' ? '已更新保存路径' : 'Path updated');
        return;
      }
      try {
        if (action === 'home') await load(workspaceRoot || '');
        if (action === 'up') await load(parentPath || currentPath || '');
      } catch (error) {
        writeOutput(String(error.message || error));
      }
    }));
    backdrop.querySelector('[data-close="true"]').addEventListener('click', () => backdrop.remove());
    backdrop.addEventListener('click', e => { if (e.target === backdrop) backdrop.remove(); });
    document.body.appendChild(backdrop);
    try {
      await load(currentPath || '');
    } catch (error) {
      writeOutput(String(error.message || error));
    }
  }

  async function apiJson(url, options) {
    const response = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...(options || {}) });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return await response.json();
  }
  function arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    const chunk = 0x8000;
    for (let i = 0; i < bytes.length; i += chunk) {
      binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
    }
    return btoa(binary);
  }
  async function apiJsonSoft(url, fallback = null, options = null) {
    try {
      const data = await apiJson(url, options || undefined);
      return { ok: true, data, error: '' };
    } catch (error) {
      return { ok: false, data: fallback, error: String(error?.message || error || 'request failed') };
    }
  }
  async function getUnifiedStatus() {
    if (window.__heyteaStatus && Date.now() - window.__heyteaStatusAt < 8000) return window.__heyteaStatus;
    window.__heyteaStatus = await apiJson('/api/unified/status');
    window.__heyteaStatusAt = Date.now();
    return window.__heyteaStatus;
  }
  async function getSyncIntervalSeconds() {
    const cached = Number(window.__heyteaSettings?.processing?.sync_interval_seconds || 0);
    if (cached > 0) return Math.max(60, cached);
    try {
      const payload = await apiJson('/api/unified/settings');
      window.__heyteaSettings = payload.settings || window.__heyteaSettings;
      const value = Number(payload.settings?.processing?.sync_interval_seconds || 3600);
      return Math.max(60, value);
    } catch (_error) {
      return 3600;
    }
  }
  function appendNotificationEvents(events) {
    if (!Array.isArray(events) || !events.length) return;
    const state = notificationState();
    const seen = new Set(state.events.map(event => String(event.id || '')));
    events.forEach(event => {
      const key = String(event.id || '');
      if (seen.has(key)) return;
      seen.add(key);
      state.events.unshift({
        id: event.id || Date.now(),
        level: event.level || 'info',
        title: event.title || 'Platform event',
        message: event.message || '',
        created_at: event.created_at || new Date().toISOString(),
      });
      state.unseen += 1;
    });
    saveNotificationState(state);
  }
  function openNotificationCenter() {
    const state = notificationState();
    const events = state.events || [];
    const title = lang() === 'zh' ? '消息中心' : 'Notification Center';
    const emptyText = lang() === 'zh' ? '暂无新消息' : 'No events yet';
    const body = events.length
      ? events.map(event => {
          const when = String(event.created_at || '').replace('T', ' ').slice(0, 19);
          return `[${event.level || 'info'}] ${event.title || ''}\n${event.message || ''}\n${when}`;
        }).join('\n\n')
      : emptyText;
    showModal(title, body);
    if (state.unseen) {
      state.unseen = 0;
      saveNotificationState(state);
    }
  }
  async function pollUnifiedEvents() {
    const lastId = parseInt(sessionStorage.getItem('heytea_last_event_id') || '0', 10);
    try {
      const payload = await apiJson(`/api/unified/events?since_id=${lastId}`);
      const events = payload.events || [];
      if (events.length) {
        const latest = events[events.length - 1];
        sessionStorage.setItem('heytea_last_event_id', String(payload.latest_id || latest.id || lastId));
        appendNotificationEvents(events);
        notify(`${latest.title || 'Platform event'}: ${latest.message || ''}`);
        refreshCollectionTasksPage(true).catch(() => {});
      } else if (payload.latest_id && payload.latest_id > lastId) {
        sessionStorage.setItem('heytea_last_event_id', String(payload.latest_id));
      }
    } catch (error) {
      clearInterval(window.__heyteaEventTimer);
    }
  }
  function startEventPolling() {
    clearInterval(window.__heyteaEventTimer);
    saveNotificationState(notificationState());
    if (!sessionStorage.getItem('heytea_last_event_id')) {
      apiJson('/api/unified/events?since_id=0').then(payload => {
        sessionStorage.setItem('heytea_last_event_id', String(payload.latest_id || 0));
      }).catch(() => {});
    } else {
      pollUnifiedEvents();
    }
    window.__heyteaEventTimer = setInterval(pollUnifiedEvents, 7000);
  }
  function collectionStatusBadge(status) {
    const value = String(status || '').toLowerCase();
    if (value.includes('success') || value.includes('finished')) return { text: translatePhrase('Success'), cls: 'bg-primary text-on-primary' };
    if (value.includes('running') || value.includes('active')) return { text: translatePhrase('Running'), cls: 'bg-[#ff9800] text-primary' };
    if (value.includes('pending') || value.includes('queued')) return { text: translatePhrase('Pending'), cls: 'bg-surface-variant text-primary border border-outline-variant' };
    if (value.includes('partial')) return { text: translatePhrase('Partial'), cls: 'bg-[#ff9800] text-primary' };
    if (value.includes('no reviews') || value.includes('empty')) return { text: lang() === 'zh' ? '无评论' : 'No Reviews', cls: 'bg-surface-variant text-primary border border-outline-variant' };
    return { text: translatePhrase('Failed'), cls: 'bg-error text-on-error' };
  }
  function formatIsoInZone(isoText, zone = tz()) {
    if (!isoText) return '-';
    const parsed = new Date(String(isoText).replace(' ', 'T'));
    if (Number.isNaN(parsed.getTime())) return String(isoText);
    const parts = getZonedParts(parsed, zone);
    return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}:${parts.second}`;
  }
  function formatTaskWhen(isoText) {
    if (!isoText) return { time: '-', day: '-' };
    const parsed = new Date(String(isoText).replace(' ', 'T'));
    if (Number.isNaN(parsed.getTime())) return { time: String(isoText), day: '' };
    const zone = tz();
    const nowDate = zonedDateString(new Date(), zone);
    const parsedDate = zonedDateString(parsed, zone);
    let day = parsedDate;
    if (parsedDate === nowDate) {
      day = translatePhrase('Today');
    } else {
      const before = new Date();
      before.setDate(before.getDate() - 1);
      if (parsedDate === zonedDateString(before, zone)) day = translatePhrase('Yesterday');
    }
    const parsedParts = getZonedParts(parsed, zone);
    return { time: `${parsedParts.hour}:${parsedParts.minute}`, day };
  }
  async function refreshCollectionTasksPage(force = false) {
    if (pageByPath() !== 'collection_tasks') return;
    if (!force && window.__heyteaCollectionAt && Date.now() - window.__heyteaCollectionAt < 4000) return;
    try {
      const [status, runsPayload, failuresPayload] = await Promise.all([
        apiJson('/api/unified/status'),
        apiJson('/api/unified/runs?limit=50'),
        apiJson('/api/unified/failures?limit=30').catch(() => ({ failures: [], error_events: [] })),
      ]);
      window.__heyteaCollectionAt = Date.now();
      const coordinator = status.coordinator || {};
      const taskFailures = Array.isArray(failuresPayload.failures) ? failuresPayload.failures : [];
      const runMap = new Map((runsPayload.runs || []).map(run => [run.run_id, run]));
      const rows = [];
      (coordinator.active || []).forEach(active => {
        rows.push({
          id: active.run_id || active.key || `ACTIVE-${Date.now()}`,
          platform: platformLabel(active.platform || active.key || ''),
          geo: active.account || '-',
          scope: 'All Active JDE',
          mode: active.dry_run ? 'Dry Run' : 'Immediate',
          status: 'Running',
          extracted: '-',
          failed: '-',
          when: active.started_at || '',
          run: runMap.get(active.run_id || ''),
        });
      });
      (coordinator.history || []).forEach(hist => {
        const run = runMap.get(hist.run_id || '');
        rows.push({
          id: hist.run_id || hist.key || `HIS-${Date.now()}`,
          platform: platformLabel((hist.key || '').split(':')[0] || ''),
          geo: (hist.key || '').split(':')[1] || '-',
          scope: 'All Active JDE',
          mode: hist.dry_run ? 'Dry Run' : 'Immediate',
          status: hist.ok ? 'Success' : 'Failed',
          extracted: (run?.review_count ?? hist.reviews ?? '-'),
          failed: (run?.error_count ?? ((hist.errors || []).length) ?? '-'),
          when: hist.finished_at || hist.started_at || run?.updated_at || '',
          run,
        });
      });
      (runsPayload.runs || []).forEach(run => {
        if (rows.some(row => row.id === run.run_id)) return;
        const runHealth = String(run.health_status || '').toLowerCase();
        let runStatus = (run.last_stage || '').toLowerCase().includes('finish') ? 'Success' : 'Pending';
        if (runHealth === 'failed') runStatus = 'Failed';
        else if (runHealth === 'partial') runStatus = 'Partial';
        else if (runHealth === 'empty') runStatus = 'No Reviews';
        else if (runHealth === 'running') runStatus = 'Running';
        rows.push({
          id: run.run_id || '-',
          platform: run.platform ? platformLabel(run.platform) : '-',
          geo: run.account || '-',
          scope: 'Run Artifact',
          mode: 'Immediate',
          status: runStatus,
          extracted: run.review_count ?? '-',
          failed: run.error_count ?? '-',
          when: run.updated_at || '',
          run,
        });
      });
      JSON.parse(localStorage.getItem('heytea_tasks') || '[]').slice(0, 5).forEach(task => {
        if (rows.some(row => row.id === task.id)) return;
        rows.push({
          id: task.id,
          platform: task.platform || '-',
          geo: (task.countries || []).join(', ') || '-',
          scope: 'All Active JDE',
          mode: task.mode || 'Immediate',
          status: 'Queued',
          extracted: '-',
          failed: '-',
          when: task.created_at || '',
          run: null,
        });
      });
      const unique = [];
      const seen = new Set();
      rows.forEach(row => {
        const key = `${row.id}|${row.status}`;
        if (seen.has(key)) return;
        seen.add(key);
        unique.push(row);
      });
      const tbody = document.querySelector('main table tbody');
      if (tbody) {
        tbody.innerHTML = unique.slice(0, 30).map(row => {
          const badge = collectionStatusBadge(row.status);
          const when = formatTaskWhen(row.when);
          const actionIcon = row.run?.has_normalized_reviews ? 'download' : 'receipt_long';
          return `<tr class="border-b border-outline-variant hover:bg-surface-bright transition-colors">
            <td class="py-2 px-3 font-data-mono text-data-mono text-primary">${escapeHtml(row.id || '-')}</td>
            <td class="py-2 px-3"><div class="font-semibold text-primary">${escapeHtml(row.platform || '-')}</div><div class="text-secondary text-[11px]">${escapeHtml(row.geo || '-')}</div></td>
            <td class="py-2 px-3 text-secondary">${escapeHtml(row.scope || '-')}</td>
            <td class="py-2 px-3 text-secondary">${escapeHtml(row.mode || '-')}</td>
            <td class="py-2 px-3"><span class="inline-flex items-center justify-center ${badge.cls} font-label-caps text-[10px] px-2 py-0.5 uppercase tracking-wide w-auto max-w-full text-center">${escapeHtml(badge.text)}</span></td>
            <td class="py-2 px-3 text-right"><div class="font-data-mono text-data-mono">${escapeHtml(String(row.extracted ?? '-'))}</div><div class="text-secondary text-[11px] font-data-mono text-data-mono">${escapeHtml(String(row.failed ?? '-'))} ${escapeHtml(translatePhrase('Failed').toLowerCase())}</div></td>
            <td class="py-2 px-3 text-secondary"><div>${escapeHtml(when.time)}</div><div class="text-[11px]">${escapeHtml(when.day)}</div></td>
            <td class="py-2 px-3 text-center"><button class="text-primary hover:text-secondary transition-colors" data-task-row-id="${escapeHtml(row.id || '')}" title="Run detail"><span class="material-symbols-outlined text-[18px]">${actionIcon}</span></button></td>
          </tr>`;
        }).join('');
        tbody.querySelectorAll('button[data-task-row-id]').forEach(button => {
          button.addEventListener('click', () => {
            const row = unique.find(item => item.id === button.dataset.taskRowId);
            if (!row) return;
            showModal(lang() === 'zh' ? '\u4efb\u52a1\u8be6\u60c5' : 'Task Detail', JSON.stringify(row, null, 2));
          });
        });
      }
      const cards = Array.from(document.querySelectorAll('main .font-display-lg')).slice(0, 4);
      if (cards.length >= 4) {
        const history = coordinator.history || [];
        const successRuns = history.filter(item => item.ok).length;
        const failedRuns = history.filter(item => !item.ok).length;
        const totalRuns = Math.max(1, history.length);
        const reviewCount = history.reduce((acc, item) => acc + Number(item.reviews || 0), 0);
        cards[0].textContent = String(coordinator.active_count || 0);
        cards[1].textContent = Number(reviewCount || 0).toLocaleString();
        cards[2].textContent = String(failedRuns);
        cards[3].textContent = `${((successRuns / totalRuns) * 100).toFixed(1)}%`;
      }
      const main = document.querySelector('main');
      if (main) {
        let failurePanel = document.getElementById('heytea-task-failure-panel');
        if (!failurePanel) {
          failurePanel = document.createElement('section');
          failurePanel.id = 'heytea-task-failure-panel';
          failurePanel.className = 'mt-4 bg-surface-container-lowest border border-outline p-4 space-y-3';
          const table = main.querySelector('table');
          (table?.closest('section') || main).after(failurePanel);
        }
        const failureRows = taskFailures.slice(0, 8).map(item => {
          const suggestions = (item.retry_suggestions || []).slice(0, 3).map(text => `<li>${escapeHtml(translateDynamicText(text))}</li>`).join('');
          const errors = (item.errors || []).slice(0, 2).map(text => `<div class="text-[11px] text-error break-all">${escapeHtml(text)}</div>`).join('');
          return `<div class="border border-outline-variant p-3">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <div class="font-title-sm text-primary">${escapeHtml(platformLabel(item.platform || item.platform_label || '-'))} · ${escapeHtml(String(item.account || '-'))}</div>
                <div class="text-[11px] text-secondary font-data-mono">${escapeHtml(String(item.run_id || '-'))} · ${escapeHtml(formatIsoInZone(item.updated_at || ''))}</div>
              </div>
              <button type="button" class="px-2 py-1 border border-outline-variant text-primary text-body-sm" data-failure-diagnose="${escapeHtml(item.platform || '')}">${escapeHtml(lang() === 'zh' ? '诊断' : 'Diagnose')}</button>
            </div>
            ${errors || `<div class="text-[11px] text-secondary">${escapeHtml(lang() === 'zh' ? '无明确错误体，按空结果/字段缺失处理。' : 'No explicit error body; treat as empty result or missing fields.')}</div>`}
            <div class="mt-2 text-body-sm text-secondary">${escapeHtml(lang() === 'zh' ? '重试建议' : 'Retry suggestions')}</div>
            <ul class="list-disc pl-5 text-body-sm text-secondary">${suggestions || `<li>${escapeHtml(lang() === 'zh' ? '重新检查登录态、日期筛选和只读详情入口。' : 'Recheck session, date filter and read-only detail entry.')}</li>`}</ul>
          </div>`;
        }).join('');
        failurePanel.innerHTML = `
          <div class="flex items-center justify-between gap-3">
            <div>
              <h3 class="font-title-sm text-title-sm text-primary">${escapeHtml(lang() === 'zh' ? '失败门店 / 平台重试清单' : 'Failed Stores / Platform Retry Queue')}</h3>
              <p class="text-body-sm text-secondary">${escapeHtml(lang() === 'zh' ? '由正式任务运行结果自动回填；用于人工门、重试与平台连接排障。' : 'Auto-filled from real task runs for manual gates, retries and connectivity triage.')}</p>
            </div>
            <span class="font-data-mono text-data-mono text-secondary">${Number(taskFailures.length || 0)}</span>
          </div>
          <div class="space-y-2">${failureRows || `<div class="text-body-sm text-secondary">${escapeHtml(lang() === 'zh' ? '暂无失败项。' : 'No failed items.')}</div>`}</div>`;
        failurePanel.querySelectorAll('[data-failure-diagnose]').forEach(button => button.addEventListener('click', async () => {
          const platform = button.dataset.failureDiagnose || '';
          try {
            const result = await apiJson('/api/unified/platform-diagnose', { method: 'POST', body: JSON.stringify({ platform, use_ai: false }) });
            showModal(lang() === 'zh' ? '平台诊断' : 'Platform Diagnosis', JSON.stringify(result, null, 2));
          } catch (error) {
            showModal(lang() === 'zh' ? '平台诊断失败' : 'Platform Diagnosis Failed', String(error.message || error));
          }
        }));
      }
    } catch (error) {
      notify(`Collection task refresh failed: ${error.message || error}`);
    }
  }
  function platformFromUi(label) {
    const text = String(label || '').toLowerCase();
    if (text.includes('hungry')) return 'hungry_panda';
    if (text.includes('fantuan')) return 'fantuan';
    if (text.includes('grab')) return 'grabfood';
    if (text.includes('google')) return 'google_maps';
    if (text.includes('keeta')) return 'keeta';
    if (text.includes('openrice')) return 'openrice';
    if (text.includes('mfood')) return 'mfood';
    if (text.includes('dianping') || text.includes('点评')) return 'dianping';
    if (text.includes('uber')) return 'uber_eats';
    if (text.includes('aomi') || text.includes('澳觅')) return 'aomi';
    return 'google_maps';
  }
  function formatStatus(status) {
    const platforms = Object.values(status.platforms || {}).map(p => `${p.name}: ${p.executor} | detail=${p.supports_order_detail ? 'Y' : 'N'} | images=${p.supports_review_images ? 'Y' : 'N'}`).join('\n');
    const counts = Object.entries(status.platform_counts || {}).map(([k, v]) => `${k}: ${v}`).join('\n');
    return `Stores: ${status.store_count}\nTasks: ${(status.tasks || []).join(', ')}\n\nPlatform store coverage:\n${counts || 'No registry'}\n\nExecutors:\n${platforms}\n\nCoordinator:\nactive=${status.coordinator?.active_count || 0}, real_concurrency=${status.coordinator?.real_concurrency || 1}, dry_run_concurrency=${status.coordinator?.dry_run_concurrency || 8}\n\nSafety denied actions:\n${(status.safety?.denied || []).join(', ')}`;
  }
  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  const platformMeta = {
    google_maps: { label: 'Google Maps', short: 'Google', icon: 'pin_drop', url: 'https://www.google.com/maps' },
    hungry_panda: { label: 'Hungry Panda', short: 'H. Panda', icon: 'takeout_dining', url: 'https://merchant-usa.hungrypanda.co/order/appraise' },
    fantuan: { label: 'Fantuan', short: 'Fantuan', icon: 'pedal_bike', url: 'https://merchant.fantuan.ca/#/login' },
    grabfood: { label: 'GrabFood', short: 'GrabFood', icon: 'delivery_dining', url: 'https://merchant.grab.com/portal?source=mrc' },
    keeta: { label: 'KeeTa', short: 'KeeTa', icon: 'storefront', url: 'https://merchant.mykeeta.com/m/web/order#/index' },
    openrice: { label: 'OpenRice', short: 'OpenRice', icon: 'restaurant', url: 'https://www.openrice.com/zh/hongkong/restaurants?chainId=10006678&tabIndex=0' },
    mfood: { label: 'Mfood', short: 'Mfood', icon: 'ramen_dining', url: 'https://merchant.o2o.mfoodapp.com/#/appraise/tackout' },
    dianping: { label: 'Dianping', short: 'Dianping', icon: 'reviews', url: 'https://www.dianping.com' },
    aomi: { label: 'Aomi', short: 'Aomi', icon: 'local_mall', url: 'https://merchant.aomiapp.com/#/customer/evaluation' },
    uber_eats: { label: 'Uber Eats', short: 'Uber', icon: 'two_wheeler', url: 'https://merchants.ubereats.com' }
  };
  function platformLabel(key) {
    const canonical = canonicalUiPlatform(key);
    return platformMeta[canonical]?.label || String(key || '').replace(/_/g, ' ');
  }
  function canonicalUiPlatform(value) {
    const key = String(value || '').toLowerCase().trim().replace(/\s+/g, '_').replace(/-/g, '_');
    if (key === 'hungrypanda') return 'hungry_panda';
    if (key === 'googlemaps') return 'google_maps';
    if (key === 'grab_food') return 'grabfood';
    if (key === 'open_rice') return 'openrice';
    if (key === 'ubereats' || key === 'uber') return 'uber_eats';
    return key;
  }
  function translatePhrase(text) {
    const source = String(text || '').trim();
    if (!source) return source;
    const lowerMap = lang() === 'zh' ? textZhLower : textEnLower;
    const targetMap = lang() === 'zh' ? textZh : textEn;
    return normalizeRegionText(lookupText(targetMap, lowerMap, source) || source);
  }
  function translateDynamicText(text) {
    const source = String(text ?? '').trim();
    if (!source) return '';
    const direct = translatePhrase(source);
    if (direct !== source || lang() !== 'zh') return normalizeComplianceText(direct);
    const byPhrase = replacePhrases(source, textZh);
    return normalizeComplianceText(byPhrase || source);
  }
  function storeLocation(store) {
    const country = normalizeRegionText(String(store.country || '').trim());
    const city = normalizeRegionText(String(store.city || '').trim());
    if (country && city && city !== country) return `${country}, ${city}`;
    return country || city || '-';
  }
  function storePlatformKeys(store) {
    return Object.keys(store.platforms || {}).map(canonicalUiPlatform).filter(Boolean);
  }
  function platformEntryUrl(key, pdata) {
    return (pdata && pdata.url) || platformMeta[canonicalUiPlatform(key)]?.url || '';
  }
  function normalizeComplianceText(value) {
    return normalizeLegacyYearText(normalizeRegionText(value));
  }
  function enforceComplianceTextNodes() {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;
        if (parent.closest('script, style, svg, code, pre, .material-symbols-outlined')) return NodeFilter.FILTER_REJECT;
        const text = node.nodeValue || '';
        if (!text.trim()) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(node => {
      const next = normalizeComplianceText(node.nodeValue || '');
      if (next !== (node.nodeValue || '')) node.nodeValue = next;
    });
  }
  function deterministicMetric(seed, min, max) {
    const text = String(seed || '');
    let hash = 0;
    for (let index = 0; index < text.length; index += 1) hash = (hash * 31 + text.charCodeAt(index)) >>> 0;
    return min + (hash % (max - min + 1));
  }
  function parseReviewDate(value) {
    const text = String(value || '').trim();
    if (!text) return null;
    const candidates = [text.slice(0, 10), text.replace(/\//g, '-').slice(0, 10)];
    for (const token of candidates) {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(token)) continue;
      const date = new Date(`${token}T00:00:00`);
      if (!Number.isNaN(date.getTime())) return date;
    }
    return null;
  }
  function reviewMergedText(review) {
    return `${review.review || ''} ${review.translated_review || ''}`.toLowerCase();
  }
  const keywordNoiseWords = new Set([
    'the', 'and', 'for', 'with', 'that', 'this', 'was', 'were', 'have', 'has', 'from', 'very', 'just', 'but', 'you',
    'your', 'our', 'their', 'they', 'been', 'delivery', 'drink', 'comment', 'review', 'order', 'service', 'food',
    'local', 'guide', 'reviews', 'photos', 'photo', 'ago', 'new', 'star', 'stars', 'rating', 'rated', 'minutes',
    'minute', 'hours', 'hour', 'days', 'day', 'item', 'items', 'qty', 'quantity', 'price', 'subtotal', 'total',
    '评论', '評論', '则评论', '則評論', '配送', '门店', '客服', '这个', '那个', '我们', '你们', '他们', '因为', '但是', '没有',
    '分钟', '分鐘', '分钟前', '分鐘前', '小时', '小時', '小时前', '小時前', '天前', '新', '照片', '评分', '星', '颗星', '顆星',
    '订单', '订单号', '訂單', '商品', '规格', '規格', '数量', '數量', '单价', '單價', '价格', '價格', '小计', '小計',
    '标准', '標準', '甜度', '茶底', '调整', '調整', '状态', '狀態', '推荐', '推薦', '冰沙', '少少少甜', '去茶底',
    '条评价', '條評價', '則評價', '则评价', '在地嚮導', '本地向导', '張相片', '张照片', '週前', '周前',
    '您好', '我们深表歉意', '我们深感抱歉', '感謝您', '谢谢您', 'app', 'heytea', 'tea', 'there', 'added',
    'making', 'drinking', 'even', 'though', 'requested', 'bubble', 'straw', 'impossible', 'pretty', 'good',
    'hey', 'sam', 'chen', 'nguyen', '此致', '好的', '然而', '而且', '个字', '好吧'
  ]);
  const businessKeywordRules = [
    ['缺少吸管/餐具', ['straw', '吸管', '餐具', 'accessories', 'utensil']],
    ['漏单少件', ['少给', '少了', '漏', 'missing', 'missed', '只给', '只給', '少杯', '少一杯', '少两杯', '少兩杯']],
    ['杯型/规格不符', ['大杯', '小杯', '杯子大小', '大小不一致', 'wrong size', 'size', '规格不符', '規格不符']],
    ['等待过久', ['等了', '等待', '太慢', '慢', 'delay', 'late', 'wait', '超时', '超時']],
    ['包装问题', ['包装', '包裝', '漏洒', '漏灑', 'spill', 'spilled', 'seal', '袋子', '破损', '破損']],
    ['口味正向', ['好喝', '味道很好', '味道很棒', '太棒了', '好茶', 'tasty', 'delicious', 'love', 'nice']],
    ['口味/甜度问题', ['太甜', '不甜', '没味', '沒有味', 'no taste', 'sweet', 'bitter', 'underwhelming', '不好喝']],
    ['服务态度问题', ['服务', '服務', '态度', '態度', 'rude', 'staff', 'employee', '客服']],
    ['价格/性价比', ['贵', '貴', 'pricey', 'expensive', 'worth', '性价比', '性價比']],
    ['食品安全风险', ['异物', '異物', '发霉', '發霉', '变质', '變質', 'hair', 'mold', 'spoiled', 'bug', '吐口水']],
    ['个性化需求/备注', ['生日', '蜡烛', '蠟燭', 'candle', 'birthday', '备注', '備註', 'request']],
    ['商品热度/复购', ['每次都点', '每次都點', '必点', '必點', 'go to', 'go-to', 'favorite', 'favourite', '常点', '常點']],
  ];
  const keywordModeLabels = {
    all: { zh: '全部业务主题', en: 'All Business Themes' },
    risk: { zh: '风险/投诉', en: 'Risk & Complaints' },
    fulfillment: { zh: '履约/错漏', en: 'Fulfillment' },
    product: { zh: '产品/口味', en: 'Product & Taste' },
    service: { zh: '服务/价格', en: 'Service & Value' },
    unique: { zh: '个性化需求', en: 'Unique Requests' },
  };
  function keywordModeLabel(mode) {
    const item = keywordModeLabels[mode] || keywordModeLabels.all;
    return lang() === 'zh' ? item.zh : item.en;
  }
  function keywordMatchesMode(label, mode = 'all') {
    if (!mode || mode === 'all') return true;
    const value = String(label || '');
    const groups = {
      risk: /食品安全|包装问题|等待过久|漏单少件|缺少吸管|杯型|规格|甜度问题/,
      fulfillment: /缺少吸管|漏单少件|杯型|规格|等待过久|包装问题/,
      product: /口味|甜度|商品热度|复购/,
      service: /服务态度|价格|性价比/,
      unique: /个性化需求|备注/,
    };
    return (groups[mode] || groups.all || /.*/).test(value);
  }
  function cleanReviewTextForAnalysis(review) {
    const candidates = [review?.review, review?.translated_review];
    for (const raw of candidates) {
      let text = String(raw || '').trim();
      if (!text || ['-', 'none', 'null', 'no data', '暂无', '暂无数据'].includes(text.toLowerCase())) continue;
      text = text
        .replace(/[\ue000-\uf8ff]/g, ' ')
        .replace(/\b\d+\s*(?:reviews?|photos?|stars?|minutes?|hours?|days?)\b/gi, ' ')
        .replace(/\d+\s*(?:则评论|則評論|张照片|張照片|分钟前|分鐘前|小时前|小時前|天前)/g, ' ')
        .replace(/\b(?:local guide|new|ago)\b/gi, ' ')
        .replace(/(?:订单号|訂單號|order\s*(?:id|no\.?|number|#))\s*[:：#]?\s*[A-Z]{0,6}\d{6,}/gi, ' ')
        .replace(/\s+/g, ' ')
        .trim();
      if (text.length >= 2 && !/^[\d\s:：/\-.,，。]+$/.test(text)) return text;
    }
    return '';
  }
  function keywordFrequencyFromText(text, limit = 12) {
    const normalized = String(text || '').toLowerCase();
    const terms = [];
    const english = normalized.match(/[a-z][a-z'-]{2,}/g) || [];
    const chinese = normalized.match(/[\u4e00-\u9fff]{2,}/g) || [];
    terms.push(...english, ...chinese);
    const stopwords = new Set([
      'the', 'and', 'for', 'with', 'that', 'this', 'was', 'were', 'have', 'has', 'from', 'very', 'just', 'but', 'you',
      'your', 'our', 'their', 'they', 'been', 'delivery', 'drink', 'comment', 'review', 'order', 'service', 'food',
      '\u8bc4\u8bba', '\u5ba2\u670d', '\u914d\u9001', '\u5e97\u94fa', '\u996e\u54c1', '\u53ef\u4ee5', '\u975e\u5e38',
      '\u8fd9\u4e2a', '\u90a3\u4e2a', '\u6211\u4eec', '\u4f60\u4eec', '\u4ed6\u4eec', '\u56e0\u4e3a', '\u4f46\u662f', '\u6ca1\u6709'
    ]);
    const counts = new Map();
    terms.forEach(term => {
      if (stopwords.has(term) || keywordNoiseWords.has(term) || /^\d+[a-z]*$/i.test(term) || /(分钟|分鐘|小时|小時|天前|週前|周前|评论|評論|評價|评价|照片|相片|向导|嚮導|订单|訂單|规格|規格|数量|數量|价格|價格|歉意|抱歉)/.test(term)) return;
      counts.set(term, (counts.get(term) || 0) + 1);
    });
    return Array.from(counts.entries()).sort((a, b) => b[1] - a[1]).slice(0, limit);
  }
  function keywordFrequency(reviews, limit = 12, mode = 'all') {
    const businessCounts = new Map();
    (Array.isArray(reviews) ? reviews : []).forEach(review => {
      const text = cleanReviewTextForAnalysis(review).toLowerCase();
      if (!text) return;
      businessKeywordRules.forEach(([label, needles]) => {
        if (!keywordMatchesMode(label, mode)) return;
        if (needles.some(needle => text.includes(String(needle).toLowerCase()))) {
          businessCounts.set(label, (businessCounts.get(label) || 0) + 1);
        }
      });
    });
    const business = Array.from(businessCounts.entries()).sort((a, b) => b[1] - a[1]);
    return business.slice(0, limit);
  }
  function buildDailyVolumeLocal(reviews, days, rangeStart = '', rangeEnd = '') {
    const safeDays = days === 30 ? 30 : 7;
    const end = rangeEnd ? new Date(`${rangeEnd}T00:00:00`) : new Date();
    end.setHours(0, 0, 0, 0);
    const start = rangeStart ? new Date(`${rangeStart}T00:00:00`) : new Date(end);
    start.setHours(0, 0, 0, 0);
    if (!rangeStart || Number.isNaN(start.getTime()) || !rangeEnd || Number.isNaN(end.getTime()) || start > end) {
      start.setTime(end.getTime());
      start.setDate(end.getDate() - safeDays + 1);
    }
    const span = Math.max(1, Math.min(30, Math.floor((end.getTime() - start.getTime()) / 86400000) + 1));
    const rows = [];
    const counters = new Map();
    for (let offset = 0; offset < span; offset += 1) {
      const day = new Date(start);
      day.setDate(start.getDate() + offset);
      const token = day.toISOString().slice(0, 10);
      rows.push(token);
      counters.set(token, 0);
    }
    reviews.forEach(review => {
      const date = parseReviewDate(review.review_time);
      if (!date) return;
      const token = date.toISOString().slice(0, 10);
      if (!counters.has(token)) return;
      counters.set(token, Number(counters.get(token) || 0) + 1);
    });
    return rows.map(date => ({ date, count: Number(counters.get(date) || 0) }));
  }
  function reviewDateToken(review) {
    const date = parseReviewDate(review?.review_time);
    return date ? date.toISOString().slice(0, 10) : '';
  }
  function dashboardDateReviewsHtml(date, reviews) {
    const rows = (reviews || []).filter(review => reviewDateToken(review) === date).slice(0, 12);
    if (!rows.length) {
      return `<div class="text-secondary text-body-sm">${escapeHtml(lang() === 'zh' ? '该日期暂无评论。' : 'No reviews on this date.')}</div>`;
    }
    return rows.map(review => {
      const text = cleanReviewTextForAnalysis(review) || reviewShort(review.review || review.translated_review || '-', 160);
      const rating = reviewRating(review) || '-';
      return `<div class="border border-outline-variant p-2 mb-2">
        <div class="flex justify-between gap-2 text-[11px] text-secondary">
          <span>${escapeHtml(platformLabel(review.platform || '-'))} · ${escapeHtml(String(review.store || review.store_id || '-'))}</span>
          <span>${escapeHtml(String(rating))}</span>
        </div>
        <div class="text-body-sm text-primary mt-1">${escapeHtml(reviewShort(text, 180))}</div>
      </div>`;
    }).join('');
  }
  function renderDashboardTrendSvg(trendRows, zoom = 1) {
    const rows = Array.isArray(trendRows) ? trendRows : [];
    if (!rows.length) return `<div class="text-secondary">${escapeHtml(lang() === 'zh' ? '暂无趋势数据' : 'No trend data')}</div>`;
    const safeZoom = Math.max(0.8, Math.min(3, Number(zoom || 1)));
    const width = Math.max(640, Math.round(rows.length * 92 * safeZoom));
    const height = 280;
    const left = 46;
    const right = 24;
    const top = 26;
    const bottom = 46;
    const innerW = width - left - right;
    const innerH = height - top - bottom;
    const maxCount = Math.max(1, ...rows.map(item => Number(item.count || 0)));
    const points = rows.map((item, index) => {
      const x = left + (rows.length === 1 ? innerW / 2 : (innerW * index) / (rows.length - 1));
      const y = top + innerH - (Number(item.count || 0) / maxCount) * innerH;
      return { ...item, x, y, count: Number(item.count || 0) };
    });
    const path = points.map(point => `${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(' ');
    const grid = [0, 0.25, 0.5, 0.75, 1].map(ratio => {
      const y = top + innerH - ratio * innerH;
      const label = Math.round(maxCount * ratio);
      return `<line x1="${left}" y1="${y}" x2="${width - right}" y2="${y}" stroke="#d9d1cc" stroke-dasharray="4 4"/><text x="8" y="${y + 4}" font-size="11" fill="#6b625c">${label}</text>`;
    }).join('');
    const labels = points.map((point, index) => {
      const show = rows.length <= 10 || index % Math.ceil(rows.length / 8) === 0 || index === rows.length - 1;
      if (!show) return '';
      return `<text x="${point.x}" y="${height - 16}" font-size="11" fill="#6b625c" text-anchor="middle">${escapeHtml(String(point.date || '').slice(5))}</text>`;
    }).join('');
    const circles = points.map(point => `<g class="heytea-trend-node" data-trend-date="${escapeHtml(String(point.date || ''))}" style="cursor:pointer">
      <circle cx="${point.x}" cy="${point.y}" r="7" fill="#111" stroke="#fff" stroke-width="2"></circle>
      <text x="${point.x}" y="${point.y - 12}" font-size="11" fill="#111" text-anchor="middle">${point.count}</text>
    </g>`).join('');
    return `<svg viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-label="review trend line chart">
      <rect x="0" y="0" width="${width}" height="${height}" fill="#fff"/>
      ${grid}
      <polyline points="${path}" fill="none" stroke="#111" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>
      <line x1="${left}" y1="${top + innerH}" x2="${width - right}" y2="${top + innerH}" stroke="#111"/>
      <line x1="${left}" y1="${top}" x2="${left}" y2="${top + innerH}" stroke="#111"/>
      ${labels}
      ${circles}
    </svg>`;
  }
  function buildPlatformVolumeLocal(reviews) {
    const counts = new Map();
    reviews.forEach(review => {
      const key = canonicalUiPlatform(review.platform || 'unknown') || 'unknown';
      counts.set(key, Number(counts.get(key) || 0) + 1);
    });
    return Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1])
      .map(([platform, count]) => ({ platform, count }));
  }
  function buildClustersLocal(reviews) {
    const rules = [
      { cluster: lang() === 'zh' ? '食品安全' : 'Food Safety', re: /异物|发霉|变质|腹泻|hair|mold|spoiled|bug/i },
      { cluster: lang() === 'zh' ? '配送时效' : 'Delivery Speed', re: /慢|超时|等待|delay|late|wait/i },
      { cluster: lang() === 'zh' ? '服务态度' : 'Service Attitude', re: /服务|态度|客服|rude|service/i },
      { cluster: lang() === 'zh' ? '包装口感' : 'Packaging & Taste', re: /包装|口味|漏|洒|taste|package|spill/i },
    ];
    const counts = new Map(rules.map(rule => [rule.cluster, 0]));
    reviews.forEach(review => {
      const merged = cleanReviewTextForAnalysis(review);
      rules.forEach(rule => {
        if (rule.re.test(merged)) counts.set(rule.cluster, Number(counts.get(rule.cluster) || 0) + 1);
      });
    });
    return Array.from(counts.entries())
      .map(([cluster, count]) => ({ cluster, count }))
      .filter(item => item.count > 0)
      .sort((a, b) => b.count - a.count);
  }
  function buildInsightFallbackFromReviews(reviews, days, keywordMode = 'all', rangeStart = '', rangeEnd = '') {
    const keywords = keywordFrequency(reviews, 20, keywordMode).map(([keyword, count]) => ({ keyword, count }));
    const clusters = buildClustersLocal(reviews);
    const riskSamples = reviews
      .filter(review => {
        const score = Number(reviewRating(review) || 0);
        return (score > 0 && score <= 2) || /异物|发霉|变质|腹泻|投诉|slow|late|hair|mold|spoiled|rude/i.test(`${review.review || ''} ${review.translated_review || ''}`);
      })
      .slice(0, 20);
    const daily = buildDailyVolumeLocal(reviews, days, rangeStart, rangeEnd);
    const riskCount = riskSamples.length;
    return {
      ok: true,
      days: days === 30 ? 30 : 7,
      metrics: {
        review_count: reviews.length,
        risk_count: riskCount,
        risk_index: reviews.length ? Number((riskCount / reviews.length).toFixed(4)) : 0,
        platform_count: new Set(reviews.map(item => canonicalUiPlatform(item.platform || '')).filter(Boolean)).size,
      },
      series: {
        daily_volume: daily,
        platform_volume: buildPlatformVolumeLocal(reviews),
        keywords,
        clusters,
        lifecycle: [
          { stage: lang() === 'zh' ? '新评高发期' : 'New Review Peak', count: daily.slice(-2).reduce((sum, item) => sum + Number(item.count || 0), 0) },
          { stage: lang() === 'zh' ? '稳定跟踪期' : 'Stable Tracking', count: Math.max(0, reviews.length - daily.slice(-2).reduce((sum, item) => sum + Number(item.count || 0), 0)) },
        ],
        risk_samples: riskSamples,
      },
      ai: {
        summary: lang() === 'zh'
          ? `实时分析共覆盖 ${reviews.length} 条评论，识别风险样本 ${riskCount} 条。`
          : `Realtime analysis covers ${reviews.length} reviews and identifies ${riskCount} risk samples.`,
        key_findings: keywords.slice(0, 3).map(item => `${item.keyword} (${item.count})`),
        actions: [
          lang() === 'zh' ? '优先复核低评分与带图评论。' : 'Prioritize low-rating reviews with evidence images.',
          lang() === 'zh' ? '对高风险关键词门店提高复采频率。' : 'Increase recrawl frequency for stores with high-risk keywords.',
        ],
        risk_level: riskCount > 0 ? 'medium' : 'low',
        trend_observation: '',
        lifecycle_stage: '',
        complaint_clusters: clusters.map(item => item.cluster).slice(0, 4),
        food_safety_issues: keywords.filter(item => /食品安全|异物|发霉|变质|hair|mold|spoiled/i.test(item.keyword)).map(item => item.keyword).slice(0, 6),
      },
      ai_used: false,
      ai_error: 'fallback_local_insight',
    };
  }
  function buildNotableDetailRows(reviews, limit = 8) {
    const rows = [];
    (Array.isArray(reviews) ? reviews : []).forEach(review => {
      const text = cleanReviewTextForAnalysis(review);
      if (!text) return;
      const rating = Number(reviewRating(review) || 0);
      const uniqueHint = /生日|蜡烛|蠟燭|candle|birthday|备注|備註|少给|少了|漏|missing|wrong|没有|沒有|not worth|impossible|requested/i.test(text);
      if (!uniqueHint && !(rating > 0 && rating <= 2)) return;
      rows.push({
        time: review.review_time || '-',
        platform: platformLabel(review.platform || '-'),
        store: review.store || review.store_id || '-',
        rating: rating || '-',
        text,
      });
    });
    return rows.slice(0, limit);
  }
  function buildProductDemandLocal(reviews, limit = 8) {
    const liked = new Map();
    const disliked = new Map();
    (Array.isArray(reviews) ? reviews : []).forEach(review => {
      const rating = Number(reviewRating(review) || 0);
      const items = normalizeOrderItemsForDisplay(review.ordered_items);
      items.forEach(item => {
        const name = String(orderedItemName(item) || '').trim();
        if (!name || name === '-') return;
        if (rating >= 4) liked.set(name, Number(liked.get(name) || 0) + 1);
        if (rating > 0 && rating <= 2) disliked.set(name, Number(disliked.get(name) || 0) + 1);
      });
    });
    const toRows = map => Array.from(map.entries()).sort((a, b) => b[1] - a[1]).slice(0, limit).map(([name, count]) => ({ name, count }));
    return { liked: toRows(liked), disliked: toRows(disliked) };
  }
  function computeQualityMetricsLocal(reviews, history, days) {
    const safeReviews = Array.isArray(reviews) ? reviews : [];
    const safeHistory = Array.isArray(history) ? history : [];
    const safeDays = days === 30 ? 30 : 7;
    const startDate = new Date();
    startDate.setHours(0, 0, 0, 0);
    startDate.setDate(startDate.getDate() - safeDays + 1);
    const total = safeReviews.length;
    const required = ['platform', 'store', 'review_time', 'rating', 'review'];
    let filledSlots = 0;
    let withImage = 0;
    let outOfBounds = 0;
    let orderRows = 0;
    let orderWithDetail = 0;
    let duplicateRows = 0;
    const seen = new Set();
    safeReviews.forEach(review => {
      const snapshot = {
        platform: String(review.platform || '').trim(),
        store: String(review.store || '').trim(),
        review_time: String(review.review_time || '').trim(),
        rating: String(review.rating ?? '').trim(),
        review: String(review.review || review.translated_review || '').trim(),
      };
      required.forEach(field => {
        const value = String(snapshot[field] || '').trim();
        if (value && value !== '-' && value.toLowerCase() !== 'null' && value.toLowerCase() !== 'none') filledSlots += 1;
      });
      const imageText = String(review.image_urls || '').trim();
      const hasImage = Boolean(review.has_image) || (Array.isArray(review.image_urls) && review.image_urls.length > 0) || (imageText && imageText !== '-');
      if (hasImage) withImage += 1;
      const parsed = parseReviewDate(review.review_time);
      if (parsed && parsed < startDate) outOfBounds += 1;
      const hasOrderHint = Boolean(review.has_order) || Boolean(String(review.order_id || review.order_sn || '').trim());
      if (hasOrderHint) {
        orderRows += 1;
        const detailText = String(review.order_detail || '').trim();
        const itemsText = String(review.ordered_items_text || '').trim();
        const itemsRaw = review.ordered_items;
        if ((detailText && detailText !== '-') || (itemsText && itemsText !== '-') || (Array.isArray(itemsRaw) && itemsRaw.length > 0)) {
          orderWithDetail += 1;
        }
      }
      const dedupeKey = reviewIdentityKey(review);
      if (seen.has(dedupeKey)) duplicateRows += 1;
      else seen.add(dedupeKey);
    });
    let manualGate = 0;
    let totalErrors = 0;
    safeHistory.forEach(item => {
      const errors = Array.isArray(item?.errors) ? item.errors : (item?.errors ? [item.errors] : []);
      totalErrors += errors.filter(Boolean).length;
      if (errors.some(message => /captcha|manual|blocked|forbidden|write|login/i.test(String(message || '')))) {
        manualGate += 1;
      }
    });
    const slots = Math.max(1, total * required.length);
    return {
      field_completion_rate: Number(((filledSlots / slots) * 100).toFixed(1)),
      detail_coverage: Number(((orderWithDetail / Math.max(1, orderRows)) * 100).toFixed(1)),
      image_coverage: Number(((withImage / Math.max(1, total)) * 100).toFixed(1)),
      duplicate_rate: Number(((duplicateRows / Math.max(1, total)) * 100).toFixed(2)),
      out_of_bounds_count: outOfBounds,
      manual_gate_count: manualGate,
      total_errors: totalErrors,
      review_count: total,
    };
  }
  function stateBadge(state) {
    const key = String(state || 'pending').toLowerCase();
    if (key === 'success') return { label: translatePhrase('Success'), cls: 'bg-primary text-on-primary' };
    if (key === 'running') return { label: translatePhrase('Running'), cls: 'bg-[#ff9800] text-primary' };
    if (key === 'partial') return { label: translatePhrase('Partial'), cls: 'bg-[#ff9800] text-primary' };
    if (key === 'failed') return { label: translatePhrase('Failed'), cls: 'bg-error text-on-error' };
    return { label: translatePhrase('Pending'), cls: 'bg-surface-variant text-primary border border-outline-variant' };
  }
  function derivePlatformStates(status, runs) {
    const states = {};
    Object.keys(status.platforms || {}).forEach(key => { states[canonicalUiPlatform(key)] = { state: 'pending', detail: 'No run yet' }; });
    (runs || []).forEach(run => {
      const key = canonicalUiPlatform(run.platform || '');
      if (!key) return;
      let state = 'pending';
      if ((run.last_stage || '').toLowerCase().includes('running')) state = 'running';
      else if (Number(run.error_count || 0) > 0 && Number(run.review_count || 0) > 0) state = 'partial';
      else if (Number(run.error_count || 0) > 0) state = 'failed';
      else if ((run.last_stage || '').toLowerCase().includes('finish') || Number(run.review_count || 0) > 0) state = 'success';
      const detail = run.quality_error || run.last_stage || '';
      states[key] = { state, detail, run };
    });
    return states;
  }
  async function initDashboardPage() {
    if (pageByPath() !== 'dashboard') return;
    const renderSeq = nextDashboardRenderSeq();
    try {
      document.querySelectorAll('[data-i18n="action_view_all"]').forEach(button => {
        if (button.dataset.viewAllBound === '1') return;
        button.dataset.viewAllBound = '1';
        button.addEventListener('click', event => {
          event.preventDefault();
          location.href = '/stitch-static/review_workbench_global/code.html';
        });
      });
      const days = selectedDays();
      const dashboardRange = dashboardRangeState(days);
      const rangeQuery = `days=${dashboardRange.span}&start_date=${encodeURIComponent(dashboardRange.start)}&end_date=${encodeURIComponent(dashboardRange.end)}`;
      const insightTimeoutMs = 2800;
      const reviews30TimeoutMs = 2800;
      const safeInsightPromise = apiJson(`/api/unified/insight?${rangeQuery}&limit=1600`).catch(() => ({
        ok: false,
        days: dashboardRange.span,
        metrics: { review_count: 0, risk_count: 0, risk_index: 0, platform_count: 0 },
        series: { daily_volume: [], platform_volume: [], keywords: [], clusters: [], lifecycle: [], risk_samples: [] },
        ai: { summary: '', key_findings: [], root_causes: [], actions: [], risk_level: 'low' },
        ai_used: false,
        ai_error: 'insight endpoint unavailable',
      }));
      const insightFastPromise = Promise.race([
        safeInsightPromise,
        new Promise(resolve => setTimeout(() => resolve({
          ok: false,
          days: dashboardRange.span,
          metrics: { review_count: 0, risk_count: 0, risk_index: 0, platform_count: 0 },
          series: { daily_volume: [], platform_volume: [], keywords: [], clusters: [], lifecycle: [], risk_samples: [] },
          ai: { summary: '', key_findings: [], root_causes: [], actions: [], risk_level: 'low' },
          ai_used: false,
          ai_error: `insight timeout ${insightTimeoutMs}ms`,
        }), insightTimeoutMs)),
      ]);
      const safeReviews30Promise = Promise.race([
        apiJson(`/api/unified/reviews?days=30&start_date=${encodeURIComponent(defaultDashboardRange(30).start)}&end_date=${encodeURIComponent(defaultDashboardRange(30).end)}&limit=1200`).catch(() => ({ reviews: [] })),
        new Promise(resolve => setTimeout(() => resolve({ reviews: [] }), reviews30TimeoutMs)),
      ]);
      const [status, runsPayload, registryPayload, reviewsPayload, reviews30Payload] = await Promise.all([
        apiJson('/api/unified/status'),
        apiJson('/api/unified/runs?limit=100'),
        apiJson('/api/unified/stores?limit=1000'),
        apiJson(`/api/unified/reviews?${rangeQuery}&limit=600`),
        safeReviews30Promise,
      ]);
      if (!isActiveDashboardRender(renderSeq)) return;
      const reviews = dedupeReviewRecords(reviewsPayload.reviews || []);
      const reviews30 = dedupeReviewRecords(reviews30Payload.reviews || []);
      const runs = runsPayload.runs || [];
      const insight = buildInsightFallbackFromReviews(reviews, dashboardRange.span, 'all', dashboardRange.start, dashboardRange.end);
      const states = derivePlatformStates(status, runs);

      const cards = Array.from(document.querySelectorAll('main .font-display-lg')).slice(0, 6);
      const negativeCount = reviews.filter(review => {
        const score = Number(reviewRating(review) || 0);
        return (score > 0 && score <= 2) || /异物|发霉|变质|投诉|slow|late|hair|mold|spoiled|rude/i.test(`${review.review || ''} ${review.translated_review || ''}`);
      }).length;
      const lowRatingCount = reviews.filter(review => Number(reviewRating(review) || 0) > 0 && Number(reviewRating(review) || 0) <= 3).length;
      const imageCount = reviews.filter(review => review.has_image).length;
      const translatedCount = reviews.filter(review => Boolean(reviewTranslationText(review))).length;
      const failedStoreCount = new Set((runs || []).filter(run => Number(run.error_count || 0) > 0).map(run => `${run.platform || ''}:${run.account || ''}`)).size;
      if (cards[0]) cards[0].textContent = Number(reviews.length).toLocaleString();
      if (cards[1]) cards[1].textContent = Number(negativeCount).toLocaleString();
      if (cards[2]) cards[2].textContent = Number(lowRatingCount).toLocaleString();
      if (cards[3]) cards[3].textContent = Number(imageCount).toLocaleString();
      if (cards[4]) cards[4].textContent = Number(translatedCount).toLocaleString();
      if (cards[5]) cards[5].textContent = Number(failedStoreCount).toLocaleString();

      const parsedDates = reviews30.map(review => parseReviewDate(review.review_time)).filter(Boolean);
      const today = new Date();
      const start7 = new Date(today); start7.setDate(today.getDate() - 6);
      const prev7Start = new Date(today); prev7Start.setDate(today.getDate() - 13);
      const prev7End = new Date(today); prev7End.setDate(today.getDate() - 7);
      const thisWeek = parsedDates.filter(date => date >= start7).length;
      const lastWeek = parsedDates.filter(date => date >= prev7Start && date <= prev7End).length;
      const thisMonth = parsedDates.filter(date => date.getMonth() === today.getMonth() && date.getFullYear() === today.getFullYear()).length;
      const lastMonthDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      const lastMonth = parsedDates.filter(date => date.getMonth() === lastMonthDate.getMonth() && date.getFullYear() === lastMonthDate.getFullYear()).length;
      const wowDelta = lastWeek ? (((thisWeek - lastWeek) / lastWeek) * 100).toFixed(1) : '-';
      const momDelta = lastMonth ? (((thisMonth - lastMonth) / lastMonth) * 100).toFixed(1) : '-';

      const byPlatform = {};
      reviews.forEach(review => {
        const key = canonicalUiPlatform(review.platform || '');
        byPlatform[key] = (byPlatform[key] || 0) + 1;
      });
      const platformRows = Object.entries(byPlatform).sort((a, b) => b[1] - a[1]).slice(0, 8);
      const keywords = keywordFrequency(reviews, 10);
      const chartTitleNode = document.querySelector('[data-i18n="chart_title_volume_vs_negative"]');
      if (chartTitleNode) chartTitleNode.textContent = lang() === 'zh' ? '多维评论趋势与关键词洞察' : 'Multi-dimensional Review Trends & Keyword Insights';
      const legendVolume = document.querySelector('[data-i18n="chart_legend_volume"]');
      if (legendVolume) legendVolume.textContent = lang() === 'zh' ? '评论量' : 'Review Volume';
      const legendNegative = document.querySelector('[data-i18n="chart_legend_negative_rate"]');
      if (legendNegative) legendNegative.textContent = lang() === 'zh' ? '关键词热度' : 'Keyword Heat';
      const chartPlaceholderNode = document.querySelector('[data-i18n="chart_placeholder_text"]');
      const chartBoxEnhanced = chartPlaceholderNode?.parentElement;
      if (chartBoxEnhanced) {
        const trendRows = Array.isArray(insight.series?.daily_volume) ? insight.series.daily_volume : [];
        const platformRowsRich = Array.isArray(insight.series?.platform_volume)
          ? insight.series.platform_volume
          : platformRows.map(([platform, count]) => ({ platform, count }));
        const keywordRows = Array.isArray(insight.series?.keywords)
          ? insight.series.keywords
          : keywords.map(([keyword, count]) => ({ keyword, count }));
        const clusterRows = Array.isArray(insight.series?.clusters) ? insight.series.clusters : [];
        const aiInsight = insight.ai || {};
        const zoom = Math.max(0.8, Math.min(3, Number(window.__heyteaDashboardTrendZoom || 1)));
        const defaultTrendDate = [...trendRows].reverse().find(item => Number(item.count || 0) > 0)?.date || trendRows[trendRows.length - 1]?.date || new Date().toISOString().slice(0, 10);
        const selectedTrendDate = window.__heyteaDashboardTrendDate || defaultTrendDate;
        const safeTrendDate = trendRows.some(item => item.date === selectedTrendDate) ? selectedTrendDate : defaultTrendDate;
        window.__heyteaDashboardTrendDate = safeTrendDate;
        const maxTrend = Math.max(1, ...trendRows.map(item => Number(item.count || 0)));
        const maxPlatform = Math.max(1, ...platformRowsRich.map(item => Number(item.count || 0)));
        const maxKeyword = Math.max(1, ...keywordRows.map(item => Number(item.count || 0)));
        const maxCluster = Math.max(1, ...clusterRows.map(item => Number(item.count || 0)));
        const activeChartView = String(window.__heyteaDashboardChartView || localStorage.getItem('heytea_dashboard_chart_view') || 'trend');
        const phaseText = lang() === 'zh'
          ? `本地趋势已加载（${dashboardRange.start} 至 ${dashboardRange.end}），AI洞察补全中...`
          : `Local trend loaded (${dashboardRange.start} to ${dashboardRange.end}), AI insight syncing...`;
        chartBoxEnhanced.innerHTML = `
          <div class="w-full h-full overflow-auto p-4 space-y-4">
            <div class="border border-outline-variant bg-surface-container-low px-3 py-2 text-body-sm text-secondary" data-dashboard-phase-banner>${escapeHtml(phaseText)}</div>
            <div class="flex flex-wrap gap-2">
              <button class="px-2 py-1 border border-outline-variant text-body-sm" data-chart-view="trend">${lang() === 'zh' ? '趋势折线' : 'Trend'}</button>
              <button class="px-2 py-1 border border-outline-variant text-body-sm" data-chart-view="platform">${lang() === 'zh' ? '平台分布' : 'Platform'}</button>
              <button class="px-2 py-1 border border-outline-variant text-body-sm" data-chart-view="keywords">${lang() === 'zh' ? '词频热表' : 'Keywords'}</button>
              <button class="px-2 py-1 border border-outline-variant text-body-sm" data-chart-view="clusters">${lang() === 'zh' ? '主题聚类' : 'Clusters'}</button>
              <button class="px-2 py-1 border border-primary text-primary text-body-sm" data-chart-view="ai">${lang() === 'zh' ? 'AI解读' : 'AI Insight'}</button>
              <button class="px-2 py-1 border border-primary text-primary text-body-sm" data-dashboard-open-ai>${lang() === 'zh' ? '打开AI分析页' : 'Open AI Analysis'}</button>
              <button class="px-2 py-1 border border-outline-variant text-body-sm" data-trend-zoom="out">− ${lang() === 'zh' ? '缩小' : 'Zoom out'}</button>
              <button class="px-2 py-1 border border-outline-variant text-body-sm" data-trend-zoom="in">+ ${lang() === 'zh' ? '放大' : 'Zoom in'}</button>
              <label class="flex items-center gap-1 text-body-sm text-secondary ml-auto">${lang() === 'zh' ? '起始' : 'Start'}
                <input type="date" class="border border-outline-variant px-2 py-1 text-body-sm" data-trend-range-start value="${escapeHtml(dashboardRange.start)}">
              </label>
              <label class="flex items-center gap-1 text-body-sm text-secondary">${lang() === 'zh' ? '结束' : 'End'}
                <input type="date" class="border border-outline-variant px-2 py-1 text-body-sm" data-trend-range-end value="${escapeHtml(dashboardRange.end)}">
              </label>
              <button class="px-2 py-1 border border-outline-variant text-body-sm" data-trend-range-apply>${lang() === 'zh' ? '应用' : 'Apply'}</button>
              <button class="px-2 py-1 border border-outline-variant text-body-sm" data-trend-range-reset>${lang() === 'zh' ? '重置' : 'Reset'}</button>
              <label class="flex items-center gap-1 text-body-sm text-secondary">${lang() === 'zh' ? '节点日期' : 'Date'}
                <input type="date" class="border border-outline-variant px-2 py-1 text-body-sm" data-trend-date-input value="${escapeHtml(safeTrendDate)}">
              </label>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div class="border border-outline-variant p-3">
                <div class="font-label-caps text-label-caps text-secondary mb-2">${lang() === 'zh' ? '本周 / 上周 评论量' : 'This Week / Last Week'}</div>
                <div class="font-data-mono text-data-mono text-primary">${thisWeek} / ${lastWeek}</div>
                <div class="text-body-sm text-secondary">${lang() === 'zh' ? '周环比' : 'WoW'}: ${wowDelta === '-' ? '-' : `${wowDelta}%`}</div>
              </div>
              <div class="border border-outline-variant p-3">
                <div class="font-label-caps text-label-caps text-secondary mb-2">${lang() === 'zh' ? '本月 / 上月 评论量' : 'This Month / Last Month'}</div>
                <div class="font-data-mono text-data-mono text-primary">${thisMonth} / ${lastMonth}</div>
                <div class="text-body-sm text-secondary">${lang() === 'zh' ? '月环比' : 'MoM'}: ${momDelta === '-' ? '-' : `${momDelta}%`}</div>
              </div>
            </div>
            <div data-chart-panel="trend" style="${activeChartView === 'trend' ? '' : 'display:none'}">
              <div class="font-label-caps text-label-caps text-secondary mb-2">${lang() === 'zh' ? '评论趋势折线图（点击节点查看当天评论）' : 'Review Trend Line (click nodes for reviews)'}</div>
              <div class="overflow-auto border border-outline-variant bg-white">${renderDashboardTrendSvg(trendRows, zoom)}</div>
              <div class="mt-3 border border-outline-variant p-2">
                <div class="font-label-caps text-label-caps text-secondary mb-2" data-selected-trend-label>${escapeHtml((lang() === 'zh' ? '选中日期：' : 'Selected date: ') + safeTrendDate)}</div>
                <div data-dashboard-date-reviews>${dashboardDateReviewsHtml(safeTrendDate, reviews)}</div>
              </div>
            </div>
            <div data-chart-panel="platform" style="${activeChartView === 'platform' ? '' : 'display:none'}">
              <div class="font-label-caps text-label-caps text-secondary mb-2">${lang() === 'zh' ? '平台评论分布' : 'Platform Review Distribution'}</div>
              ${platformRowsRich.map(item => `<div class="flex items-center gap-2 mb-1"><div class="w-36 truncate text-body-sm text-primary">${escapeHtml(platformLabel(item.platform || ''))}</div><div class="flex-1 h-2 bg-surface-container-high"><div class="h-2 bg-primary" style="width:${Math.max(6, Math.round((Number(item.count || 0) / maxPlatform) * 100))}%"></div></div><div class="w-12 text-right font-data-mono text-data-mono">${Number(item.count || 0)}</div></div>`).join('') || `<div class="text-secondary">${lang() === 'zh' ? '暂无平台数据' : 'No platform data'}</div>`}
            </div>
            <div data-chart-panel="keywords" style="${activeChartView === 'keywords' ? '' : 'display:none'}">
              <div class="font-label-caps text-label-caps text-secondary mb-2">${lang() === 'zh' ? '关键词词频热表' : 'Keyword Frequency Heat Table'}</div>
              ${keywordRows.map(item => `<div class="flex items-center gap-2 mb-1"><div class="w-36 truncate text-body-sm text-primary">${escapeHtml(String(item.keyword || ''))}</div><div class="flex-1 h-2 bg-surface-container-high"><div class="h-2 bg-[#ff9800]" style="width:${Math.max(6, Math.round((Number(item.count || 0) / maxKeyword) * 100))}%"></div></div><div class="w-12 text-right font-data-mono text-data-mono">${Number(item.count || 0)}</div></div>`).join('') || `<div class="text-secondary">${lang() === 'zh' ? '暂无关键词' : 'No keywords'}</div>`}
            </div>
            <div data-chart-panel="clusters" style="${activeChartView === 'clusters' ? '' : 'display:none'}">
              <div class="font-label-caps text-label-caps text-secondary mb-2">${lang() === 'zh' ? '主题聚类分布' : 'Topic Clusters'}</div>
              ${clusterRows.map(item => `<div class="flex items-center gap-2 mb-1"><div class="w-36 truncate text-body-sm text-primary">${escapeHtml(String(item.cluster || ''))}</div><div class="flex-1 h-2 bg-surface-container-high"><div class="h-2 bg-[#8e44ad]" style="width:${Math.max(6, Math.round((Number(item.count || 0) / maxCluster) * 100))}%"></div></div><div class="w-12 text-right font-data-mono text-data-mono">${Number(item.count || 0)}</div></div>`).join('') || `<div class="text-secondary">${lang() === 'zh' ? '暂无聚类结果' : 'No clusters'}</div>`}
            </div>
            <div data-chart-panel="ai" style="${activeChartView === 'ai' ? '' : 'display:none'}" class="border border-outline-variant p-3">
              <div class="font-label-caps text-label-caps text-secondary mb-2">${lang() === 'zh' ? 'AI实时解读与整改建议' : 'AI Interpretation & Remediation'}</div>
              <div class="text-body-sm text-primary mb-2" data-dashboard-ai-summary>${escapeHtml(aiInsight.summary || (lang() === 'zh' ? '暂无AI解读' : 'No AI interpretation yet'))}</div>
              <div class="text-body-sm text-secondary" data-dashboard-ai-findings>${escapeHtml((aiInsight.key_findings || []).join('； '))}</div>
              <div class="text-body-sm text-secondary mt-1" data-dashboard-ai-actions>${escapeHtml((aiInsight.actions || []).join('； '))}</div>
            </div>
          </div>`;
        chartBoxEnhanced.querySelectorAll('[data-chart-view]').forEach(button => button.addEventListener('click', () => {
          const view = button.dataset.chartView;
          window.__heyteaDashboardChartView = view;
          localStorage.setItem('heytea_dashboard_chart_view', view);
          chartBoxEnhanced.querySelectorAll('[data-chart-panel]').forEach(panel => {
            panel.style.display = panel.dataset.chartPanel === view ? '' : 'none';
          });
        }));
        const showTrendDate = date => {
          const token = String(date || '').slice(0, 10);
          if (!token) return;
          window.__heyteaDashboardTrendDate = token;
          const input = chartBoxEnhanced.querySelector('[data-trend-date-input]');
          if (input) input.value = token;
          const label = chartBoxEnhanced.querySelector('[data-selected-trend-label]');
          if (label) label.textContent = (lang() === 'zh' ? '选中日期：' : 'Selected date: ') + token;
          const target = chartBoxEnhanced.querySelector('[data-dashboard-date-reviews]');
          if (target) target.innerHTML = dashboardDateReviewsHtml(token, reviews);
        };
        chartBoxEnhanced.querySelectorAll('[data-trend-date]').forEach(node => node.addEventListener('click', () => {
          showTrendDate(node.dataset.trendDate);
        }));
        chartBoxEnhanced.querySelector('[data-trend-date-input]')?.addEventListener('change', event => {
          showTrendDate(event.target.value);
          chartBoxEnhanced.querySelector('[data-chart-view="trend"]')?.click();
        });
        chartBoxEnhanced.querySelector('[data-trend-range-apply]')?.addEventListener('click', async () => {
          const start = String(chartBoxEnhanced.querySelector('[data-trend-range-start]')?.value || '').trim();
          const end = String(chartBoxEnhanced.querySelector('[data-trend-range-end]')?.value || '').trim();
          if (!/^\d{4}-\d{2}-\d{2}$/.test(start) || !/^\d{4}-\d{2}-\d{2}$/.test(end)) {
            notify(lang() === 'zh' ? '请选择合法的起止日期' : 'Please select a valid date range');
            return;
          }
          persistDashboardRange(start, end, 'custom');
          updateDynamicDateLabels();
          await initDashboardPage();
        });
        chartBoxEnhanced.querySelector('[data-trend-range-reset]')?.addEventListener('click', async () => {
          const fallback = defaultDashboardRange(selectedDays());
          persistDashboardRange(fallback.start, fallback.end, 'rolling');
          updateDynamicDateLabels();
          await initDashboardPage();
        });
        chartBoxEnhanced.querySelectorAll('[data-trend-zoom]').forEach(button => button.addEventListener('click', async () => {
          const direction = button.dataset.trendZoom;
          const current = Math.max(0.8, Math.min(3, Number(window.__heyteaDashboardTrendZoom || 1)));
          window.__heyteaDashboardTrendZoom = direction === 'in' ? Math.min(3, current + 0.25) : Math.max(0.8, current - 0.25);
          await initDashboardPage();
        }));
        chartBoxEnhanced.querySelector('[data-dashboard-open-ai]')?.addEventListener('click', () => {
          location.href = '/stitch-static/quality_report_global/code.html?focus=ai';
        });
        safeInsightPromise.then(payload => {
          if (!isActiveDashboardRender(renderSeq)) return;
          const phaseNode = chartBoxEnhanced.querySelector('[data-dashboard-phase-banner]');
          if (!payload || !payload.ok) {
            if (phaseNode) {
              phaseNode.textContent = lang() === 'zh'
                ? `本地趋势已加载（${dashboardRange.start} 至 ${dashboardRange.end}），模型洞察异常，已保留本地规则洞察。`
                : `Local trend loaded (${dashboardRange.start} to ${dashboardRange.end}); model insight failed, local rule insight remains available.`;
              return;
              phaseNode.textContent = lang() === 'zh'
                ? `本地趋势已加载（${dashboardRange.start} 至 ${dashboardRange.end}），AI洞察暂不可用。`
                : `Local trend loaded (${dashboardRange.start} to ${dashboardRange.end}), AI insight temporarily unavailable.`;
            }
            return;
          }
          const aiSummaryNode = chartBoxEnhanced.querySelector('[data-dashboard-ai-summary]');
          const aiFindingNode = chartBoxEnhanced.querySelector('[data-dashboard-ai-findings]');
          const aiActionNode = chartBoxEnhanced.querySelector('[data-dashboard-ai-actions]');
          const ai = payload.ai || {};
          if (aiSummaryNode) aiSummaryNode.textContent = String(ai.summary || aiSummaryNode.textContent || '');
          if (aiFindingNode) aiFindingNode.textContent = String((ai.key_findings || []).join('； '));
          if (aiActionNode) aiActionNode.textContent = String((ai.actions || []).join('； '));
          if (phaseNode) {
            const aiError = String(payload.ai_error || '').trim();
            const aiUsed = Boolean(payload.ai_used);
            phaseNode.textContent = lang() === 'zh'
              ? (aiUsed
                  ? `本地趋势已加载（${dashboardRange.start} 至 ${dashboardRange.end}），AI洞察已补全。`
                  : `本地趋势已加载（${dashboardRange.start} 至 ${dashboardRange.end}），模型洞察未启用或额度不足，已使用本地规则洞察。${aiError ? ` 原因：${aiError.slice(0, 120)}` : ''}`)
              : (aiUsed
                  ? `Local trend loaded (${dashboardRange.start} to ${dashboardRange.end}); AI insight synchronized.`
                  : `Local trend loaded (${dashboardRange.start} to ${dashboardRange.end}); model insight not active or quota-limited, using local rule insight.${aiError ? ` Reason: ${aiError.slice(0, 120)}` : ''}`);
            return;
            phaseNode.textContent = lang() === 'zh'
              ? `本地趋势已加载（${dashboardRange.start} 至 ${dashboardRange.end}），AI洞察已补全。`
              : `Local trend loaded (${dashboardRange.start} to ${dashboardRange.end}), AI insight synchronized.`;
          }
        }).catch(() => {});
      }

      const statusTitle = document.querySelector('[data-i18n="platform_status_title"]');
      const statusSection = statusTitle?.closest('section') || statusTitle?.parentElement;
      const statusList = statusSection?.querySelector('div.flex.flex-col.gap-3')
        || statusSection?.querySelector('div.flex.flex-col');
      if (statusList) {
        const keys = Object.keys(status.platforms || {}).map(canonicalUiPlatform);
        statusList.innerHTML = keys.map(key => {
          const badge = stateBadge(states[key]?.state || 'pending');
          const detail = normalizeComplianceText(states[key]?.detail || '');
          return `<div class="flex justify-between items-center p-3 border border-[#E0E0E0] bg-surface cursor-pointer" data-platform-status="${escapeHtml(key)}">
            <div><span class="font-body-sm text-body-sm text-primary font-medium">${escapeHtml(platformLabel(key))}</span>${detail ? `<div class="text-[11px] text-secondary mt-1">${escapeHtml(detail)}</div>` : ''}</div>
            <span class="font-label-caps text-label-caps uppercase px-2 py-[2px] ${badge.cls}">${escapeHtml(badge.label)}</span>
          </div>`;
        }).join('');
        statusList.querySelectorAll('[data-platform-status]').forEach(node => node.addEventListener('click', async () => {
          const key = node.dataset.platformStatus;
          const state = states[key] || {};
          const run = state.run || {};
          try {
            const payload = await apiJson('/api/unified/platform-diagnose', {
              method: 'POST',
              body: JSON.stringify({ platform: key, region: '' }),
            });
            showModal(
              lang() === 'zh' ? '平台连接诊断与处置建议' : 'Platform Diagnostics & Remediation',
              JSON.stringify(payload, null, 2),
            );
          } catch (_error) {
            showModal(lang() === 'zh' ? '平台连接诊断' : 'Platform Connectivity Diagnostics', JSON.stringify({ platform: platformLabel(key), state, run }, null, 2));
          }
        }));
      }

      const matrixTitle = document.querySelector('[data-i18n="matrix_title"]');
      const matrixSection = matrixTitle?.closest('section')
        || matrixTitle?.closest('div.bg-surface-container-lowest')
        || matrixTitle?.parentElement?.parentElement
        || matrixTitle?.parentElement;
      const matrixTable = matrixSection?.querySelector('table');
      const matrixBody = matrixTable?.querySelector('tbody');
      if (matrixBody) {
        const stores = registryPayload.stores || [];
        const requiredRegions = ['中国澳门', '加拿大', '马来西亚', '美国', '英国', '韩国', '澳大利亚', '中国香港'];
        const observedRegions = Array.from(new Set(stores.map(store => normalizeRegionForMatrix(String(store.country || ''))).filter(Boolean)));
        const extraRegions = observedRegions.filter(region => !requiredRegions.includes(region));
        const regions = [...requiredRegions, ...extraRegions];
        const preferredPlatformColumns = [
          'google_maps',
          'grabfood',
          'hungry_panda',
          'fantuan',
          'keeta',
          'openrice',
          'mfood',
          'dianping',
          'uber_eats',
          'aomi',
        ];
        const observedPlatformSet = new Set(
          Object.keys(status.platforms || {}).map(canonicalUiPlatform).filter(Boolean),
        );
        stores.forEach(store => {
          storePlatformKeys(store).forEach(key => observedPlatformSet.add(key));
        });
        const platformColumns = [
          ...preferredPlatformColumns.filter(key => observedPlatformSet.has(key)),
          ...Array.from(observedPlatformSet).filter(key => !preferredPlatformColumns.includes(key)).sort(),
        ];
        const matrixHeadRow = matrixTable?.querySelector('thead tr');
        if (matrixHeadRow) {
          matrixHeadRow.innerHTML = [
            `<th>${escapeHtml(lang() === 'zh' ? '区域' : 'Region')}</th>`,
            ...platformColumns.map(platformKey => `<th>${escapeHtml(platformLabel(platformKey))}</th>`),
          ].join('');
        }
        const colorByState = {
          success: 'bg-primary border border-primary',
          failed: 'bg-error border border-error',
          partial: 'bg-[#FF9800] border border-[#FF9800]',
          running: 'bg-[#FF9800] border border-[#FF9800]',
          pending: 'bg-[#E0E0E0] border border-[#BDBDBD]',
        };
        matrixBody.innerHTML = regions.map(region => {
          const storesInRegion = stores.filter(store => normalizeRegionForMatrix(String(store.country || '')) === region);
          const cellHtml = platformColumns.map(platformKey => {
            const hasStore = storesInRegion.some(store => storePlatformKeys(store).includes(platformKey));
            const state = hasStore ? (states[platformKey]?.state || 'pending') : 'pending';
            const cls = hasStore ? (colorByState[state] || colorByState.pending) : 'bg-[#F5F5F5] border border-[#E0E0E0]';
            return `<td class="py-2 px-3"><span class="w-3 h-3 inline-block ${cls}"></span></td>`;
          }).join('');
          return `<tr class="table-row-divider"><td class="py-2 px-3 font-medium">${escapeHtml(region)}</td>${cellHtml}</tr>`;
        }).join('');
      }

      const exceptionsTitle = document.querySelector('[data-i18n="exceptions_title"]');
      const exceptionList = exceptionsTitle?.parentElement?.nextElementSibling;
      if (exceptionList) {
        const risky = reviews
          .filter(review => {
            const score = Number(reviewRating(review) || 0);
            if (score > 0 && score <= 3) return true;
            return /hair|bug|mold|spoiled|sick|异物|发霉|变质|腹泻|投诉|慢|漏|错|差评/i.test(`${review.review || ''} ${review.translated_review || ''}`);
          })
          .filter((review, index, all) => {
            const key = `${reviewStore(review)}|${reviewPlatform(review)}|${String(review.review || review.translated_review || '').slice(0, 120)}`;
            return all.findIndex(item => `${reviewStore(item)}|${reviewPlatform(item)}|${String(item.review || item.translated_review || '').slice(0, 120)}` === key) === index;
          })
          .slice(0, 5);
        if (risky.length) {
          exceptionList.innerHTML = risky.map(review => {
            const score = Number(reviewRating(review) || 0);
            const starScore = Math.max(1, Math.min(5, Math.round(score || 1)));
            const tag = reviewQuality(review);
            return `<div class="p-4 border-b border-[#E0E0E0] hover:bg-surface transition-colors cursor-pointer border-l-4 ${score <= 2 ? 'border-l-error' : 'border-l-[#FF9800]'}">
              <div class="flex justify-between items-start mb-2 gap-2">
                <div class="flex flex-wrap items-center gap-2">
                  <span class="font-label-caps text-label-caps bg-primary text-on-primary px-1 whitespace-nowrap">${escapeHtml(reviewStore(review))}</span>
                  <span class="font-data-mono text-data-mono text-secondary whitespace-nowrap">${escapeHtml(platformLabel(review.platform))}</span>
                </div>
                <div class="font-data-mono text-data-mono ${score <= 2 ? 'text-error' : 'text-[#FF9800]'} font-bold text-[16px] whitespace-nowrap">${'\u2605'.repeat(starScore)}${'\u2606'.repeat(5 - starScore)}</div>
              </div>
              <p class="font-body-sm text-body-sm text-primary mb-2 line-clamp-2">${escapeHtml(reviewShort(review.review || review.translated_review || '-'))}</p>
              <div class="flex flex-wrap gap-2"><span class="font-label-caps text-label-caps text-on-secondary-container bg-surface-container-high px-2 py-0.5 border border-[#E0E0E0] whitespace-nowrap">${escapeHtml(tag)}</span></div>
            </div>`;
          }).join('');
        }
      }
      enforceComplianceTextNodes();
    } catch (error) {
      notify(`Dashboard refresh failed: ${error.message || error}`);
    }
  }
  async function initPlatformMatrixPage() {
    if (pageByPath() !== 'platform_matrix') return;
    try {
      const [status, runsPayload] = await Promise.all([
        apiJson('/api/unified/status'),
        apiJson('/api/unified/runs?limit=120'),
      ]);
      const runs = runsPayload.runs || [];
      const states = derivePlatformStates(status, runs);
      const tbody = document.querySelector('main table tbody');
      if (tbody) {
        const rows = Object.entries(status.platforms || {}).map(([rawKey, capability]) => {
          const key = canonicalUiPlatform(rawKey);
          const badge = stateBadge(states[key]?.state || 'pending');
          const login = capability.supports_login ? (lang() === 'zh' ? '需登录' : 'Login') : (lang() === 'zh' ? '免登录' : 'No Login');
          const strategy = Array.isArray(capability.strategies) ? capability.strategies.join(' / ') : '-';
          return `<tr class="hover:bg-surface-container-low transition-colors" data-platform-row="${escapeHtml(key)}">
            <td class="px-3 py-2 font-medium text-primary">${escapeHtml(normalizeComplianceText(capability.name || platformLabel(key)))}</td>
            <td class="px-3 py-2 text-secondary font-data-mono text-data-mono">${escapeHtml(capability.executor || '-')}</td>
            <td class="px-3 py-2 text-secondary">${escapeHtml(login)}</td>
            <td class="px-3 py-2 text-secondary">${escapeHtml(strategy)}</td>
            <td class="px-3 py-2 text-center">${capability.supports_order_detail ? '\u2713' : '\u2717'}</td>
            <td class="px-3 py-2 text-center">${capability.supports_review_images ? '\u2713' : '\u2717'}</td>
            <td class="px-3 py-2 text-center">${capability.supports_translation_source ? '\u2713' : '\u2717'}</td>
            <td class="px-3 py-2 text-center">${capability.human_gate_required ? '\u2713' : '\u2717'}</td>
            <td class="px-3 py-2 text-secondary text-center">${escapeHtml(formatTaskWhen(states[key]?.run?.updated_at || '').time || '-')}</td>
            <td class="px-3 py-2 text-right"><span class="inline-flex items-center px-2 py-0.5 ${badge.cls} font-label-caps text-[10px] uppercase">${escapeHtml(badge.label)}</span></td>
            <td class="px-3 py-2 text-right"><button type="button" data-platform-diagnose="${escapeHtml(key)}" class="text-primary underline hover:text-secondary">${lang() === 'zh' ? '诊断' : 'Diagnose'}</button></td>
          </tr>`;
        });
        tbody.innerHTML = rows.join('');
        tbody.querySelectorAll('[data-platform-diagnose]').forEach(button => button.addEventListener('click', async () => {
          const key = button.dataset.platformDiagnose;
          const capability = status.platforms?.[key] || status.platforms?.[Object.keys(status.platforms || {}).find(item => canonicalUiPlatform(item) === key)];
          const state = states[key] || {};
          try {
            const payload = await apiJson('/api/unified/platform-diagnose', {
              method: 'POST',
              body: JSON.stringify({ platform: key, region: '' }),
            });
            showModal(lang() === 'zh' ? '连接诊断与AI处置' : 'Connectivity Diagnostics & AI Remediation', JSON.stringify(payload, null, 2));
          } catch (_error) {
            showModal(lang() === 'zh' ? '连接诊断' : 'Connectivity Diagnostics', JSON.stringify({ platform: platformLabel(key), capability, state }, null, 2));
          }
        }));
      }
      const failureTitle = Array.from(document.querySelectorAll('main h4')).find(node => cleanText(node).toLowerCase().includes('recent failures') || cleanText(node).includes('最近失败'));
      const failureContainer = failureTitle?.parentElement?.querySelector('ul, .space-y-2');
      if (failureContainer) {
        const failedRuns = runs.filter(run => Number(run.error_count || 0) > 0).slice(0, 6);
        failureContainer.innerHTML = failedRuns.length
          ? failedRuns.map(run => `<li class="text-body-sm text-secondary"><strong class="text-primary">${escapeHtml(platformLabel(run.platform || '-'))}</strong> · ${escapeHtml(normalizeComplianceText(run.account || '-'))} · ${escapeHtml(String(run.error_count || 0))} ${lang() === 'zh' ? '错误' : 'errors'}</li>`).join('')
          : `<li class="text-body-sm text-secondary">${lang() === 'zh' ? '暂无失败记录' : 'No recent failures'}</li>`;
      }
      enforceComplianceTextNodes();
    } catch (error) {
      notify(`Platform matrix refresh failed: ${error.message || error}`);
    }
  }

  function labelForRoute(route) { return lang() === 'zh' ? route[2] : route[1]; }
  function normalizeLayout() {
    const active = pageByPath();
    const nav = document.querySelector('body > nav, div > nav, nav');
    if (nav) {
      nav.setAttribute('data-heytea-nav', 'true');
      nav.className = 'fixed left-0 top-0 h-full z-40 bg-surface-container-lowest border-r border-outline-variant flex flex-col';
      nav.innerHTML = `
        <div class="heytea-nav-brand"><h1>HEYTEA</h1><p>${translatePhrase('Overseas Review')}</p></div>
        <div class="heytea-nav-list flex-1 flex flex-col">
          ${routes.map(route => `<a class="${route[0] === active ? 'is-active' : ''}" href="${route[4]}" target="_self"><span class="material-symbols-outlined">${route[3]}</span><span>${labelForRoute(route)}</span></a>`).join('')}
        </div>
        <div class="heytea-nav-footer flex flex-col">
          <button class="heytea-export" type="button" data-action="export-report"><span class="material-symbols-outlined" style="font-size:15px;vertical-align:-3px;margin-right:6px">download</span>${translatePhrase('Export Report')}</button>
          <a href="/stitch-static/safety_audit_global/code.html?view=settings"><span class="material-symbols-outlined">settings</span><span>${t('settings')}</span></a>
          <a href="/stitch-static/safety_audit_global/code.html?view=knowledge"><span class="material-symbols-outlined">help</span><span>${t('help')}</span></a>
        </div>`;
    }
    document.querySelectorAll('[class*="ml-[240px]"], [class*="md:ml-[240px]"]').forEach(el => el.classList.add('heytea-main-normalized'));
  }
  function normalizeHeader() {
    const header = document.querySelector('body header:not(.heytea-modal header), header:not(.heytea-modal header)');
    if (!header) return;
    header.setAttribute('data-heytea-header', 'true');
    header.className = '';
    const tzOptions = timezones.map(([zone, label]) => `<option value="${zone}" ${zone === tz() ? 'selected' : ''}>${label}</option>`).join('');
    const englishLabel = lang() === 'zh' ? '\u82f1\u6587' : 'English';
    const chineseLabel = '\u4e2d\u6587';
    header.innerHTML = `
      <div class="heytea-header-left">
        <span class="heytea-header-title">${t('title')}</span>
        <span class="heytea-header-range" data-heytea-live-range>${liveRangeLabel()}</span>
        <span class="heytea-readonly-badge"><span class="material-symbols-outlined" style="font-size:16px">lock</span>${t('readonly')}</span>
      </div>
      <div class="heytea-header-right">
        <div class="heytea-clock" title="Time is converted from Beijing reference time"><span class="heytea-clock-label">${t('clock')}</span><span class="heytea-clock-time" id="heytea-live-clock">--</span></div>
        <select class="heytea-header-select" id="heytea-timezone-select" aria-label="${t('timezone')}">${tzOptions}</select>
        <select class="heytea-header-select" id="heytea-language-select" aria-label="Language"><option value="en" ${lang()==='en'?'selected':''}>${englishLabel}</option><option value="zh" ${lang()==='zh'?'selected':''}>${chineseLabel}</option></select>
        <button class="heytea-header-button" type="button" data-action="weekly-range"><span class="material-symbols-outlined" style="font-size:18px">calendar_today</span>${t('weekly')}: <strong data-heytea-days="${selectedDays()}">${selectedRangeLabel()}</strong></button>
        <button class="heytea-header-button" type="button" data-action="ai-analysis">${lang() === 'zh' ? 'AI分析' : 'AI Analysis'}</button>
        <button class="heytea-header-button primary" type="button" data-action="export-report">${t('export')}</button>
        <span class="heytea-header-divider"></span>
        <button class="heytea-header-icon" type="button" data-action="notifications" title="${t('notifications')}"><span class="material-symbols-outlined">notifications</span><span class="heytea-notify-badge" id="heytea-notify-badge" hidden></span></button>
        <button class="heytea-header-icon" type="button" title="${t('profile')}"><span class="material-symbols-outlined">account_circle</span></button>
      </div>`;
    document.getElementById('heytea-timezone-select')?.addEventListener('change', e => { localStorage.setItem('heytea_timezone', e.target.value); updateClock(); updateDynamicDateLabels(); notify(t('tzChanged')); });
    document.getElementById('heytea-language-select')?.addEventListener('change', e => { localStorage.setItem('heytea_lang', e.target.value); normalizeLayout(); normalizeHeader(); applyLanguage(); updateDynamicDateLabels(); notify(t('langChanged')); });
    saveNotificationState(notificationState());
    updateDynamicDateLabels();
  }
  function updateClock() {
    const node = document.getElementById('heytea-live-clock');
    const label = document.querySelector('.heytea-clock-label');
    if (!node) return;
    const zone = tz();
    const now = new Date();
    const parts = getZonedParts(now, zone);
    node.textContent = `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}:${parts.second}`;
    if (label) {
      const zoneLabel = zone === BEIJING_ZONE ? t('clock') : (timezones.find(([z]) => z === zone)?.[1] || zone);
      const offsetText = formatUtcOffset(zoneOffsetMinutes(now, zone));
      label.textContent = `${zoneLabel} (${offsetText})`;
      label.title = describeDeltaFromBeijing(now, zone);
    }
    updateDynamicDateLabels();
  }
  function startClock() { updateClock(); clearInterval(window.__heyteaClockTimer); window.__heyteaClockTimer = setInterval(updateClock, 1000); }

  function applyFonts() {
    document.documentElement.setAttribute('data-heytea-lang', lang());
    document.documentElement.lang = lang() === 'zh' ? 'zh-CN' : 'en';
  }
  function replaceTextNode(node, nextText) {
    const original = node.__heyteaOriginalText ?? node.nodeValue;
    if (node.__heyteaOriginalText === undefined) node.__heyteaOriginalText = original;
    const leading = original.match(/^\s*/)?.[0] || '';
    const trailing = original.match(/\s*$/)?.[0] || '';
    node.nodeValue = leading + nextText + trailing;
  }
  function translateStaticText() {
    const targetMap = lang() === 'zh' ? textZh : textEn;
    const lowerMap = lang() === 'zh' ? textZhLower : textEnLower;
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.dataset.i18n;
      const keyed = i18nKeys[key]?.[lang()];
      if (keyed !== undefined) {
        el.textContent = normalizeComplianceText(keyed);
        el.dataset.heyteaI18nTranslated = '1';
        return;
      }
      if (!el.dataset.heyteaOriginalText) el.dataset.heyteaOriginalText = cleanText(el);
      const original = el.dataset.heyteaOriginalText;
      const next = lookupText(targetMap, lowerMap, original);
      if (next) {
        el.textContent = normalizeComplianceText(next);
        el.dataset.heyteaI18nTranslated = '1';
      }
    });
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;
        if (parent.closest('script, style, svg, pre, code, .material-symbols-outlined, [data-i18n], [data-no-auto-translate="true"], [data-review-id], [data-heytea-nav="true"], [data-heytea-header="true"], .heytea-clock')) return NodeFilter.FILTER_REJECT;
        const text = (node.__heyteaOriginalText ?? node.nodeValue).trim();
        if (!text || /^[\d\s.,:%()\-/:]+$/.test(text)) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      const original = node.__heyteaOriginalText ?? node.nodeValue;
      const trimmed = original.trim();
      const currentTrimmed = node.nodeValue.trim();
      const exact = lookupText(targetMap, lowerMap, trimmed) || lookupText(targetMap, lowerMap, currentTrimmed);
      const phrase = exact ? null : replacePhrases(trimmed, targetMap);
      const next = exact || (phrase && phrase !== trimmed ? phrase : null) || (lang() === 'en' ? trimmed : null);
      if (next) {
        const button = node.parentElement?.closest('button');
        if (button && !button.__heyteaOriginalText) button.__heyteaOriginalText = cleanText(button);
        replaceTextNode(node, normalizeComplianceText(next));
      }
    }
    document.querySelectorAll('button').forEach(button => {
      if (!button.__heyteaOriginalText) button.__heyteaOriginalText = cleanText(button);
      const original = button.__heyteaOriginalText.trim();
      const lowerMap = lang() === 'zh' ? textZhLower : textEnLower;
      const next = lookupText(targetMap, lowerMap, original);
      if (next && button.children.length <= 1) button.textContent = normalizeComplianceText(next);
    });
    document.querySelectorAll('input[placeholder], textarea[placeholder]').forEach(el => {
      if (!el.dataset.heyteaOriginalPlaceholder) el.dataset.heyteaOriginalPlaceholder = el.getAttribute('placeholder') || '';
      const original = el.dataset.heyteaOriginalPlaceholder;
      const lowerMap = lang() === 'zh' ? textZhLower : textEnLower;
      const next = lookupText(targetMap, lowerMap, original) || (lang() === 'en' ? original : null);
      if (next) el.setAttribute('placeholder', normalizeComplianceText(next));
    });
    enforceComplianceTextNodes();
  }
  function applyLanguage() {
    applyFonts();
    const active = pageByPath();
    const pageTitle = routes.find(r => r[0] === active);
    if (document.title && pageTitle) document.title = `${labelForRoute(pageTitle)} - Overseas Review Platform`;
    const headings = {
      dashboard: ['Global Dashboard', '\u5168\u7403\u4eea\u8868\u76d8'], collection_tasks: ['Collection Tasks', '\u91c7\u96c6\u4efb\u52a1'], store_coverage: ['Store Coverage', '\u95e8\u5e97\u8986\u76d6'], review_workbench: ['Review Workbench', '\u8bc4\u8bba\u5de5\u4f5c\u53f0'], platform_matrix: ['Platform Matrix', '\u5e73\u53f0\u77e9\u9635'], quality_report: ['Data Quality Control', '\u6570\u636e\u8d28\u91cf\u63a7\u5236'], safety_audit: ['Safety & Audit Operations', '\u5b89\u5168\u4e0e\u5ba1\u8ba1\u64cd\u4f5c']
    };
    const h = document.querySelector('main h1, main h2, .heytea-main-normalized h1, .heytea-main-normalized h2');
    if (h && headings[active]) h.textContent = lang() === 'zh' ? headings[active][1] : headings[active][0];
    translateStaticText();
    updateDynamicDateLabels();
    if (active === 'store_coverage' && window.__heyteaStoreCoverage) renderStoreCoverage();
    if (active === 'review_workbench' && window.__heyteaReviews) renderReviewWorkbench();
  }
  function initDrawer() {
    const drawer = Array.from(document.querySelectorAll('aside')).find(el => cleanText(el).includes('New Collection Task') || cleanText(el).includes('Target Definition') || cleanText(el).includes('\u65b0\u5efa\u91c7\u96c6\u4efb\u52a1') || cleanText(el).includes('\u76ee\u6807\u5b9a\u4e49'));
    if (!drawer) return;
    drawer.dataset.drawer = 'new-task';
    if (!sessionStorage.getItem('heytea-task-drawer-open')) drawer.classList.add('heytea-hidden');
    const platformSelect = drawer.querySelector('select');
    if (platformSelect && !platformSelect.dataset.heyteaPlatformsBound) {
      platformSelect.dataset.heyteaPlatformsBound = '1';
      getUnifiedStatus().then(status => {
        const keys = Object.keys(status.platforms || {});
        if (keys.length) platformSelect.innerHTML = keys.map(key => `<option value="${escapeHtml(platformLabel(key))}">${escapeHtml(platformLabel(key))}</option>`).join('');
      }).catch(() => {});
    }
    drawer.querySelectorAll('button').forEach(btn => {
      const text = cleanText(btn).toLowerCase();
      if (text.includes('close') || text.includes('cancel')) btn.addEventListener('click', e => { e.preventDefault(); drawer.classList.add('heytea-hidden'); sessionStorage.removeItem('heytea-task-drawer-open'); notify('Task panel closed.'); });
    });
  }
  function openTaskDrawer() {
    let drawer = document.querySelector('aside[data-drawer="new-task"]'); if (!drawer) drawer = Array.from(document.querySelectorAll('aside')).find(el => cleanText(el).includes('Target Definition') || cleanText(el).includes('\u76ee\u6807\u5b9a\u4e49')); if (drawer) drawer.dataset.drawer = 'new-task';
    if (drawer) { drawer.classList.remove('heytea-hidden'); sessionStorage.setItem('heytea-task-drawer-open', '1'); notify(t('taskOpened')); }
    else location.href = '/stitch-static/collection_tasks_global/code.html';
  }
  async function deployTask(scope) {
    const checkedRadio = Array.from(scope.querySelectorAll('input[type="radio"]')).find(x => x.checked);
    const platformLabel = scope.querySelector('select')?.value || 'Google Maps';
    const countrySet = new Set(['US', 'CA', 'UK', 'AU', 'SG', 'MY', 'HK', 'MO', 'KR']);
    const countries = Array.from(scope.querySelectorAll('input[type="checkbox"]:checked'))
      .map(x => cleanText(x.closest('label')))
      .map(x => String(x || '').toUpperCase())
      .filter(x => countrySet.has(x) || /^[A-Z]{2,3}$/.test(x));
    const task = { id: 'TASK-' + new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14), platform: platformLabel, countries, mode: checkedRadio?.closest('label') ? cleanText(checkedRadio.closest('label')) : 'Immediate', days: selectedDays(), safe_mode: true, timezone: tz(), language: lang(), created_at: new Date().toISOString() };
    const tasks = JSON.parse(localStorage.getItem('heytea_tasks') || '[]'); tasks.unshift(task); localStorage.setItem('heytea_tasks', JSON.stringify(tasks.slice(0, 20)));
    const isDryRun = /dry|演练|estimate/i.test(task.mode || '');
    notify(isDryRun ? `Task queued locally: ${task.platform}. Running backend dry-run...` : `Task queued locally: ${task.platform}. Starting read-only collector...`);
    try {
      const endpoint = isDryRun ? '/api/unified/dry-run' : '/api/unified/collect';
      const result = await apiJson(endpoint, { method: 'POST', body: JSON.stringify({ platform: platformFromUi(platformLabel), days: selectedDays(), dry_run: isDryRun, task }) });
      showModal(lang() === 'zh' ? '\u4efb\u52a1\u6267\u884c\u7ed3\u679c' : 'Task Execution Result', JSON.stringify({ task, backend_result: result }, null, 2) + '\n\nExecution order:\n1. Validate DSL and safety policy\n2. Acquire platform/account lock\n3. Start read-only collector\n4. Export normalized reviews and quality report\n5. Refresh Review Workbench from real exports');
      if (isDryRun) {
        notify(result.ok ? 'Backend dry-run completed.' : 'Backend dry-run failed.');
      } else {
        notify(result.accepted || result.running ? 'Read-only collection started in background.' : (result.ok ? 'Read-only collection completed.' : 'Backend task failed.'));
      }
      await refreshCollectionTasksPage(true);
    } catch (error) {
      showModal('Backend API Error', String(error));
      notify('Backend API error.');
    }
  }
  async function exportVisible() {
    let status = null;
    try { status = await getUnifiedStatus(); } catch (error) { status = { ok: false, error: String(error) }; }
    const payload = { page: document.title || location.pathname, exported_at: new Date().toISOString(), timezone: tz(), language: lang(), source: 'stitch-console-ui', active_route: pageByPath(), backend_status: status, visible_text: cleanText(document.body).slice(0, 16000), local_tasks: JSON.parse(localStorage.getItem('heytea_tasks') || '[]') };
    download('heytea-review-console-export.json', JSON.stringify(payload, null, 2), 'application/json;charset=utf-8'); notify(t('exportDone'));
  }
  async function showSettings() {
    location.href = '/stitch-static/safety_audit_global/code.html?view=settings';
  }
  function initFormState() {
    document.querySelectorAll('input[type="checkbox"], input[type="radio"]').forEach(input => {
      const update = () => { const label = input.closest('label'); if (!label) return; if (input.checked) label.classList.add('heytea-state-selected'); else label.classList.remove('heytea-state-selected'); };
      input.addEventListener('change', () => { if (input.type === 'radio' && input.name) document.querySelectorAll(`input[type="radio"][name="${CSS.escape(input.name)}"]`).forEach(peer => peer.closest('label')?.classList.remove('heytea-state-selected')); update(); }); update();
    });
    document.querySelectorAll('select:not(#heytea-timezone-select):not(#heytea-language-select)').forEach(sel => sel.addEventListener('change', () => notify(`Selected: ${sel.value}`)));
  }
  function rowDetails(target) { const row = target.closest('tr') || target.closest('[class*="border"]') || target.closest('[class*="grid"]') || target.closest('[class*="card"]'); showModal(lang() === 'zh' ? '\u8be6\u60c5\u9884\u89c8' : 'Detail Preview', row ? cleanText(row) : cleanText(document.body).slice(0, 1000)); }
  function initButtons() {
    document.addEventListener('click', async event => {
      const button = event.target.closest('button'); if (!button) return;
      if (button.closest('.heytea-settings-shell')) return;
      const text = cleanText(button); const rawText = (button.__heyteaOriginalText || button.textContent || text); const intent = (text + ' ' + rawText + ' ' + (button.getAttribute('title') || '') + ' ' + (button.dataset.action || '')).toLowerCase();
      if (text.includes('中文') || /\ben\b/.test(intent) || intent.includes('english')) {
        event.preventDefault();
        const nextLang = text.includes('中文') ? 'zh' : 'en';
        localStorage.setItem('heytea_lang', nextLang);
        normalizeLayout(); normalizeHeader(); applyLanguage();
        notify(nextLang === 'zh' ? '\u8bed\u8a00\u5df2\u5207\u6362\u4e3a\u4e2d\u6587\u3002' : 'Language switched to English.');
        return;
      }
      if (intent.includes('export')) { event.preventDefault(); await exportVisible(); return; }
      if (intent.includes('ai analysis') || intent.includes('ai分析') || button.dataset.action === 'ai-analysis') {
        event.preventDefault();
        location.href = '/stitch-static/quality_report_global/code.html?focus=ai';
        return;
      }
      if (intent.includes('new task') || intent.includes('create task') || intent.includes('launch') || intent.includes('run collector') || intent.includes('\u521b\u5efa\u65b0\u4efb\u52a1')) { event.preventDefault(); openTaskDrawer(); return; }
      if (intent.includes('weekly') || intent.includes('last 7') || intent.includes('last 30') || intent.includes('date range') || intent.includes('custom') || intent.includes('range') || intent.includes('\u65e5\u671f\u8303\u56f4')) { event.preventDefault(); showRangeModal(); return; }
      if (intent.includes('filter') || intent.includes('refresh')) { event.preventDefault(); notify(`${t('filterApplied')}: ${selectedRangeLabel()}`); return; }
      if (intent.includes('notification') || intent.includes('\u901a\u77e5') || button.dataset.action === 'notifications') { event.preventDefault(); openNotificationCenter(); return; }
      if (intent.includes('setting')) { event.preventDefault(); await showSettings(); return; }
      if (intent.includes('deploy task') || intent.includes('\u90e8\u7f72\u4efb\u52a1')) { event.preventDefault(); const drawer = button.closest('aside[data-drawer="new-task"]') || document.querySelector('aside[data-drawer="new-task"]'); if (drawer) await deployTask(drawer); return; }
      if (intent.includes('view all') || intent.includes('查看全部')) { event.preventDefault(); location.href = '/stitch-static/review_workbench_global/code.html'; return; }
      if (intent.includes('platform') || intent.includes('store') || intent.includes('coverage') || intent.includes('capability')) { event.preventDefault(); const status = await getUnifiedStatus(); showModal('Unified Backend Status', formatStatus(status)); return; }
      if (intent.includes('more') || intent.includes('detail') || intent.includes('logs') || intent.includes('edit')) { event.preventDefault(); rowDetails(button); return; }
      if (intent.includes('cancel') || intent.includes('close')) return;
      if (!button.disabled) notify(`Action acknowledged: ${text || 'button'}`);
    });
  }
  function initClickableRows() { document.querySelectorAll('tbody tr').forEach(row => row.addEventListener('dblclick', () => showModal(lang() === 'zh' ? '\u884c\u8be6\u60c5' : 'Row Detail', cleanText(row)))); }
  function initSearch() {
    document.querySelectorAll('input[type="text"], input[type="search"]').forEach(input => {
      const ph = (input.getAttribute('placeholder') || '').toLowerCase(); if (!ph.includes('search') && !ph.includes('filter')) return;
      input.addEventListener('input', () => { const q = input.value.toLowerCase().trim(); document.querySelectorAll('tbody tr').forEach(row => { row.style.display = !q || cleanText(row).toLowerCase().includes(q) ? '' : 'none'; }); });
    });
  }
  const settingLabels = {
    en: {
      title: 'System Settings',
      subtitle: 'Production controls for API providers, appearance, processing, exports, quality scoring, checkpoints and human intervention.',
      api: 'API Config',
      appearance: 'Appearance',
      processing: 'Processing',
      export: 'Export',
      quality: 'Quality',
      risk: 'Production Check',
      save: 'Save Settings',
      reset: 'Reset Defaults',
      import: 'Import Config',
      exportConfig: 'Export Config',
      cancel: 'Cancel',
      activeProvider: 'Active provider',
      apiMode: 'API mode',
      apiKey: 'API Key',
      baseUrl: 'Base URL',
      model: 'Model',
      modelParams: 'Model parameters',
      temperature: 'Temperature',
      maxTokens: 'Max Tokens',
      timeout: 'Timeout seconds',
      apiFormat: 'API format',
      testModel: 'Test Active Model',
      theme: 'Theme',
      fontFamily: 'Font family',
      fontSize: 'Font size',
      language: 'Language',
      timezone: 'Timezone',
      manualGate: 'Enable human gate',
      gateThreshold: 'Confidence threshold',
      preprocess: 'Conversation preprocessing',
      roleSplit: 'Auto role split',
      prompt: 'Classification prompt',
      batchSize: 'Batch size',
      workers: 'Parallel workers',
      apiInterval: 'API interval seconds',
      syncInterval: 'Sync interval seconds',
      checkpoint: 'Enable checkpoint resume',
      checkpointPath: 'Checkpoint path',
      autosave: 'Autosave interval minutes',
      retryCount: 'Retry count',
      retryInterval: 'Retry interval seconds',
      maxDays: 'Max collection days',
      realConcurrency: 'Real-task concurrency',
      dryConcurrency: 'Dry-run concurrency',
      outputDir: 'Default output directory',
      format: 'Default format',
      timestamp: 'Append timestamp',
      rawApi: 'Include raw API response',
      analysis: 'Include analysis result',
      charts: 'Include charts',
      images: 'Include images',
      jsonl: 'Write normalized JSONL',
      minCompleteness: 'Min field completeness',
      minDetail: 'Min order-detail coverage',
      maxDuplicate: 'Max duplicate rate',
      reward: 'Report reward weights',
      loss: 'Report loss weights',
      runCheck: 'Run Production Check',
      browseFolder: 'Choose Folder',
      knowledgeTitle: 'Quality Risk Knowledge Base',
      knowledgeBody: 'This page defines production guardrails: read-only collection, checkpoint resume, normalized JSONL, quality reports, model-audited evidence, retry candidates, and human-gate intervention.'
    },
    zh: {
      title: '\u7cfb\u7edf\u8bbe\u7f6e',
      subtitle: '\u751f\u4ea7\u7ea7\u63a7\u5236\uff1aAPI \u4f9b\u5e94\u5546\u3001\u5916\u89c2\u3001\u5904\u7406\u3001\u5bfc\u51fa\u3001\u8d28\u91cf\u6253\u5206\u3001\u65ad\u70b9\u7eed\u4f20\u548c\u4eba\u5de5\u4ecb\u5165\u3002',
      api: 'API \u914d\u7f6e',
      appearance: '\u5916\u89c2',
      processing: '\u5904\u7406',
      export: '\u5bfc\u51fa',
      quality: '\u8d28\u91cf',
      risk: '\u751f\u4ea7\u68c0\u67e5',
      save: '\u4fdd\u5b58\u8bbe\u7f6e',
      reset: '\u91cd\u7f6e\u9ed8\u8ba4',
      import: '\u5bfc\u5165\u914d\u7f6e',
      exportConfig: '\u5bfc\u51fa\u914d\u7f6e',
      cancel: '\u53d6\u6d88',
      activeProvider: '\u4e3b\u7528\u6a21\u578b',
      apiMode: 'API \u4f7f\u7528\u6a21\u5f0f',
      apiKey: 'API \u5bc6\u94a5',
      baseUrl: 'Base URL',
      model: 'Model',
      modelParams: '\u6a21\u578b\u53c2\u6570',
      temperature: 'Temperature',
      maxTokens: 'Max Tokens',
      timeout: '\u8d85\u65f6\uff08\u79d2\uff09',
      apiFormat: 'API \u683c\u5f0f',
      testModel: '\u6d4b\u8bd5\u4e3b\u7528\u6a21\u578b',
      theme: '\u4e3b\u9898',
      fontFamily: '\u5b57\u4f53',
      fontSize: '\u5b57\u4f53\u5927\u5c0f',
      language: '\u8bed\u8a00',
      timezone: '\u65f6\u533a',
      manualGate: '\u542f\u7528\u4eba\u5de5\u4ecb\u5165',
      gateThreshold: '\u7f6e\u4fe1\u5ea6\u9608\u503c',
      preprocess: '\u4f1a\u8bdd\u6587\u672c\u9884\u5904\u7406',
      roleSplit: '\u81ea\u52a8\u8bc6\u522b\u5bf9\u8bdd\u89d2\u8272',
      prompt: '\u5206\u7c7b Prompt',
      batchSize: '\u6279\u6b21\u5927\u5c0f',
      workers: '\u5e76\u884c\u5de5\u4f5c\u6570',
      apiInterval: 'API \u8c03\u7528\u95f4\u9694\uff08\u79d2\uff09',
      syncInterval: '\u5b9a\u65f6\u540c\u6b65\u95f4\u9694\uff08\u79d2\uff09',
      checkpoint: '\u542f\u7528\u65ad\u70b9\u7eed\u4f20',
      checkpointPath: '\u65ad\u70b9\u4fdd\u5b58\u8def\u5f84',
      autosave: '\u81ea\u52a8\u4fdd\u5b58\u95f4\u9694\uff08\u5206\u949f\uff09',
      retryCount: '\u91cd\u8bd5\u6b21\u6570',
      retryInterval: '\u91cd\u8bd5\u95f4\u9694\uff08\u79d2\uff09',
      maxDays: '\u6700\u5927\u91c7\u96c6\u5929\u6570',
      realConcurrency: '\u771f\u5b9e\u4efb\u52a1\u5e76\u53d1',
      dryConcurrency: '\u6f14\u7ec3\u4efb\u52a1\u5e76\u53d1',
      outputDir: '\u9ed8\u8ba4\u5bfc\u51fa\u76ee\u5f55',
      format: '\u9ed8\u8ba4\u683c\u5f0f',
      timestamp: '\u6587\u4ef6\u540d\u81ea\u52a8\u6dfb\u52a0\u65f6\u95f4\u6233',
      rawApi: '\u5305\u542b\u539f\u59cb API \u54cd\u5e94',
      analysis: '\u5305\u542b\u5206\u6790\u7ed3\u679c',
      charts: '\u5305\u542b\u56fe\u8868',
      images: '\u5305\u542b\u56fe\u7247',
      jsonl: '\u5199\u51fa\u6807\u51c6 JSONL',
      minCompleteness: '\u6700\u4f4e\u5b57\u6bb5\u5b8c\u6574\u7387',
      minDetail: '\u6700\u4f4e\u8ba2\u5355\u8be6\u60c5\u8986\u76d6',
      maxDuplicate: '\u6700\u9ad8\u91cd\u590d\u7387',
      reward: '\u62a5\u544a\u5956\u52b1\u6743\u91cd',
      loss: '\u62a5\u544a\u635f\u5931\u6743\u91cd',
      runCheck: '\u8fd0\u884c\u751f\u4ea7\u68c0\u67e5',
      browseFolder: '\u9009\u62e9\u6587\u4ef6\u5939',
      knowledgeTitle: '\u8d28\u91cf\u98ce\u9669\u77e5\u8bc6\u5e93',
      knowledgeBody: '\u672c\u9875\u5b9a\u4e49\u751f\u4ea7\u7ea7\u7ea6\u675f\uff1a\u53ea\u8bfb\u91c7\u96c6\u3001\u65ad\u70b9\u7eed\u4f20\u3001\u6807\u51c6 JSONL\u3001\u8d28\u91cf\u62a5\u544a\u3001\u6a21\u578b\u8bc1\u636e\u5ba1\u6838\u3001\u5931\u8d25\u95e8\u5e97\u91cd\u8bd5\u548c\u4eba\u5de5\u4ecb\u5165\u3002'
    }
  };
  const sl = key => (settingLabels[lang()] || settingLabels.en)[key] || settingLabels.en[key] || key;
  function getPath(obj, path) {
    return String(path).split('.').reduce((cur, key) => (cur && cur[key] !== undefined ? cur[key] : undefined), obj);
  }
  function setPath(obj, path, value) {
    const parts = String(path).split('.');
    let cur = obj;
    while (parts.length > 1) {
      const key = parts.shift();
      cur[key] = cur[key] || {};
      cur = cur[key];
    }
    cur[parts[0]] = value;
  }
  function field(path, label, value, type = 'text', attrs = '') {
    const safe = value === undefined || value === null ? '' : value;
    return `<label class="heytea-setting-field"><span>${escapeHtml(label)}</span><input type="${type}" data-setting-path="${escapeHtml(path)}" value="${escapeHtml(safe)}" ${attrs}></label>`;
  }
  function pathPickerField(path, label, value) {
    const safe = value === undefined || value === null ? '' : value;
    return `<label class="heytea-setting-field"><span>${escapeHtml(label)}</span><div class="heytea-path-picker"><input type="text" data-setting-path="${escapeHtml(path)}" value="${escapeHtml(safe)}"><button type="button" class="heytea-settings-browse" data-settings-action="browse-folder" data-target-setting-path="${escapeHtml(path)}" title="${escapeHtml(sl('browseFolder'))}"><span class="material-symbols-outlined" style="font-size:16px">folder_open</span><span>${escapeHtml(sl('browseFolder'))}</span></button></div></label>`;
  }
  function checkbox(path, label, checked) {
    return `<label class="heytea-setting-check"><input type="checkbox" data-setting-path="${escapeHtml(path)}" ${checked ? 'checked' : ''}><span>${escapeHtml(label)}</span></label>`;
  }
  function selectField(path, label, value, options) {
    return `<label class="heytea-setting-field"><span>${escapeHtml(label)}</span><select data-setting-path="${escapeHtml(path)}">${options.map(([v, text]) => `<option value="${escapeHtml(v)}" ${String(value) === String(v) ? 'selected' : ''}>${escapeHtml(text)}</option>`).join('')}</select></label>`;
  }
  function renderSettingsTabs(active) {
    const tabs = [['api', sl('api'), 'search'], ['appearance', sl('appearance'), 'settings'], ['processing', sl('processing'), 'bolt'], ['export', sl('export'), 'download'], ['quality', sl('quality'), 'target'], ['risk', sl('risk'), 'verified']];
    return `<div class="heytea-settings-tabs">${tabs.map(([key, label, icon]) => `<button type="button" data-settings-tab="${key}" class="${active === key ? 'is-active' : ''}"><span class="material-symbols-outlined">${icon}</span>${escapeHtml(label)}</button>`).join('')}</div>`;
  }
  function renderApiSettings(settings) {
    const providers = settings.api.providers || {};
    const providerOptions = Object.entries(providers).map(([key, value]) => [key, value.label || key]);
    return `<section class="heytea-settings-section">${selectField('api.active_provider', sl('activeProvider'), settings.api.active_provider, providerOptions)}${selectField('api.mode', sl('apiMode'), settings.api.mode, [['single', 'Single API'], ['dual', 'Dual verify'], ['triple', 'Triple verify']])}<button type="button" class="heytea-settings-primary" data-settings-action="model-smoke">${escapeHtml(sl('testModel'))}</button><pre class="heytea-settings-output" id="heytea-model-output"></pre><h3>${escapeHtml(sl('api'))}</h3>${Object.entries(providers).map(([key, provider]) => `<div class="heytea-provider-card"><strong>${escapeHtml(provider.label || key)}</strong>${field(`api.providers.${key}.api_key`, `${sl('apiKey')}${provider.api_key_set ? ` (${provider.api_key_masked})` : ''}`, '', 'password', 'autocomplete="off"')}${field(`api.providers.${key}.base_url`, sl('baseUrl'), provider.base_url || '')}${field(`api.providers.${key}.model`, sl('model'), provider.model || '')}${selectField(`api.providers.${key}.api_format`, sl('apiFormat'), provider.api_format || 'openai', [['openai', 'OpenAI'], ['anthropic', 'Anthropic']])}</div>`).join('')}<h3>${escapeHtml(sl('modelParams'))}</h3>${field('api.temperature', sl('temperature'), settings.api.temperature, 'number', 'step="0.01" min="0" max="2"')}${field('api.max_tokens', sl('maxTokens'), settings.api.max_tokens, 'number', 'min="1"')}${field('api.timeout_seconds', sl('timeout'), settings.api.timeout_seconds, 'number', 'min="5"')}</section>`;
  }
  function renderAppearanceSettings(settings) {
    return `<section class="heytea-settings-section">${selectField('appearance.theme', sl('theme'), settings.appearance.theme, [['light', 'Light'], ['dark', 'Dark'], ['system', 'System']])}${field('appearance.font_family', sl('fontFamily'), settings.appearance.font_family)}${field('appearance.font_size', sl('fontSize'), settings.appearance.font_size, 'number', 'min="10" max="22"')}${selectField('appearance.language', sl('language'), settings.appearance.language || lang(), [['en', 'English'], ['zh', '\u4e2d\u6587']])}${selectField('appearance.timezone', sl('timezone'), settings.appearance.timezone || tz(), timezones)}</section>`;
  }
  function renderProcessingSettings(settings) {
    const p = settings.processing;
    return `<section class="heytea-settings-section"><h3>${escapeHtml(sl('processing'))}</h3>${checkbox('processing.manual_gate_enabled', sl('manualGate'), p.manual_gate_enabled)}${field('processing.manual_gate_threshold', sl('gateThreshold'), p.manual_gate_threshold, 'number', 'step="0.01" min="0" max="1"')}${checkbox('processing.conversation_preprocess', sl('preprocess'), p.conversation_preprocess)}${checkbox('processing.auto_dialogue_role_split', sl('roleSplit'), p.auto_dialogue_role_split)}<label class="heytea-setting-field wide"><span>${escapeHtml(sl('prompt'))}</span><textarea data-setting-path="processing.classification_prompt">${escapeHtml(p.classification_prompt || '')}</textarea></label><h3>${escapeHtml('\u6279\u5904\u7406 / Batch')}</h3>${field('processing.batch_size', sl('batchSize'), p.batch_size, 'number', 'min="1"')}${field('processing.parallel_workers', sl('workers'), p.parallel_workers, 'number', 'min="1" max="8"')}${field('processing.api_interval_seconds', sl('apiInterval'), p.api_interval_seconds, 'number', 'step="0.01" min="0"')}${field('processing.sync_interval_seconds', sl('syncInterval'), p.sync_interval_seconds ?? 3600, 'number', 'step="1" min="60"')}${checkbox('processing.checkpoint_resume', sl('checkpoint'), p.checkpoint_resume)}${pathPickerField('processing.checkpoint_path', sl('checkpointPath'), p.checkpoint_path)}${field('processing.autosave_interval_minutes', sl('autosave'), p.autosave_interval_minutes, 'number', 'min="1"')}${field('processing.retry_count', sl('retryCount'), p.retry_count, 'number', 'min="0"')}${field('processing.retry_interval_seconds', sl('retryInterval'), p.retry_interval_seconds, 'number', 'min="0"')}${field('processing.max_collection_days', sl('maxDays'), p.max_collection_days, 'number', 'min="1" max="30"')}${field('processing.real_concurrency', sl('realConcurrency'), p.real_concurrency, 'number', 'min="1" max="3"')}${field('processing.dry_run_concurrency', sl('dryConcurrency'), p.dry_run_concurrency, 'number', 'min="1" max="16"')}</section>`;
  }
  function renderExportSettings(settings) {
    const e = settings.export;
    return `<section class="heytea-settings-section">${pathPickerField('export.default_output_dir', sl('outputDir'), e.default_output_dir)}${selectField('export.default_format', sl('format'), e.default_format, [['xlsx', 'xlsx'], ['csv', 'csv'], ['json', 'json'], ['jsonl', 'jsonl']])}${checkbox('export.append_timestamp', sl('timestamp'), e.append_timestamp)}${checkbox('export.include_raw_api', sl('rawApi'), e.include_raw_api)}${checkbox('export.include_analysis', sl('analysis'), e.include_analysis)}${checkbox('export.include_charts', sl('charts'), e.include_charts)}${checkbox('export.include_images', sl('images'), e.include_images)}${checkbox('export.normalized_jsonl', sl('jsonl'), e.normalized_jsonl)}</section>`;
  }
  function renderQualitySettings(settings) {
    const q = settings.quality;
    return `<section class="heytea-settings-section">${field('quality.min_field_completeness', sl('minCompleteness'), q.min_field_completeness, 'number', 'step="0.01" min="0" max="1"')}${field('quality.min_detail_coverage', sl('minDetail'), q.min_detail_coverage, 'number', 'step="0.01" min="0" max="1"')}${field('quality.max_duplicate_rate', sl('maxDuplicate'), q.max_duplicate_rate, 'number', 'step="0.001" min="0" max="1"')}<label class="heytea-setting-field wide"><span>${escapeHtml(sl('reward'))}</span><textarea data-setting-json="quality.report_reward_weights">${escapeHtml(JSON.stringify(q.report_reward_weights || {}, null, 2))}</textarea></label><label class="heytea-setting-field wide"><span>${escapeHtml(sl('loss'))}</span><textarea data-setting-json="quality.loss_weights">${escapeHtml(JSON.stringify(q.loss_weights || {}, null, 2))}</textarea></label></section>`;
  }
  function renderRiskSettings() {
    return `<section class="heytea-settings-section"><button type="button" class="heytea-settings-primary" data-settings-action="production-check">${escapeHtml(sl('runCheck'))}</button><pre class="heytea-settings-output" id="heytea-production-output"></pre></section>`;
  }
  function renderSettingsContent(settings, activeTab) {
    if (activeTab === 'api') return renderApiSettings(settings);
    if (activeTab === 'appearance') return renderAppearanceSettings(settings);
    if (activeTab === 'processing') return renderProcessingSettings(settings);
    if (activeTab === 'export') return renderExportSettings(settings);
    if (activeTab === 'quality') return renderQualitySettings(settings);
    return renderRiskSettings(settings);
  }
  function collectSettingsPatch(root) {
    const patch = {};
    root.querySelectorAll('[data-setting-path]').forEach(input => {
      let value = input.type === 'checkbox' ? input.checked : input.value;
      if (input.type === 'number') value = Number(value);
      setPath(patch, input.dataset.settingPath, value);
    });
    root.querySelectorAll('[data-setting-json]').forEach(input => {
      try { setPath(patch, input.dataset.settingJson, JSON.parse(input.value || '{}')); }
      catch (error) { throw new Error(`${input.dataset.settingJson}: ${error.message}`); }
    });
    return patch;
  }
  async function renderSettingsPage(forceTab) {
    if (pageByPath() !== 'safety_audit') return;
    const params = new URLSearchParams(location.search);
    const view = params.get('view');
    if (view === 'knowledge') {
      const main = document.querySelector('main');
      if (main) {
        const [statusRes, runsRes, checkRes, settingsRes] = await Promise.all([
          apiJsonSoft('/api/unified/status', { platforms: {}, tasks: [], store_count: 0, monitor: {}, safety: { denied: [] } }),
          apiJsonSoft('/api/unified/runs?limit=80', { runs: [] }),
          apiJsonSoft('/api/unified/production-check', { production_check: { checks: [] } }),
          apiJsonSoft('/api/unified/settings', { settings: {} }),
        ]);
        const status = statusRes.data || {};
        const runs = runsRes.data?.runs || [];
        const checks = checkRes.data?.production_check || {};
        const settings = settingsRes.data?.settings || {};
        const taskNames = status.tasks || [];
        const platformRows = Object.entries(status.platforms || {}).map(([rawKey, capability]) => {
          const key = canonicalUiPlatform(rawKey);
          const taskReady = taskNames.some(name => canonicalUiPlatform(name).includes(key));
          const run = runs.find(item => canonicalUiPlatform(item.platform || '') === key) || {};
          const state = derivePlatformStates(status, runs)[key] || { state: taskReady ? 'pending' : 'failed', detail: taskReady ? 'Task template ready' : 'Task template missing' };
          const badge = stateBadge(state.state);
          return `<tr>
            <td>${escapeHtml(platformLabel(key))}</td>
            <td>${escapeHtml(capability.executor || '-')}</td>
            <td>${capability.supports_order_detail ? '✓' : '—'}</td>
            <td>${capability.supports_review_images ? '✓' : '—'}</td>
            <td>${capability.supports_login ? (lang() === 'zh' ? '需登录/会话' : 'Login/session') : (lang() === 'zh' ? '公开页' : 'Public')}</td>
            <td>${taskReady ? '✓' : '—'}</td>
            <td>${escapeHtml(String(run.review_count ?? '-'))}</td>
            <td><span class="${badge.cls}">${escapeHtml(badge.label)}</span></td>
          </tr>`;
        }).join('');
        const failedRuns = runs.filter(run => Number(run.error_count || 0) > 0).slice(0, 8);
        const checkRows = (checks.checks || []).map(item => `<li><strong>${escapeHtml(item.id || '-')}</strong> · ${escapeHtml(item.ok ? (lang() === 'zh' ? '通过' : 'OK') : (lang() === 'zh' ? '需处理' : 'Action needed'))} · ${escapeHtml(item.message || '')}</li>`).join('');
        const failRows = failedRuns.length
          ? failedRuns.map(run => `<li><strong>${escapeHtml(platformLabel(run.platform || '-'))}</strong> · ${escapeHtml(run.account || '-')} · ${escapeHtml(String(run.error_count || 0))} ${lang() === 'zh' ? '个错误' : 'errors'} · ${escapeHtml(run.run_id || '')}</li>`).join('')
          : `<li>${lang() === 'zh' ? '暂无失败运行。' : 'No failed runs.'}</li>`;
        main.innerHTML = `
          <div class="heytea-settings-shell heytea-guide-shell">
            <div class="heytea-settings-title">
              <span class="material-symbols-outlined">help</span>
              <div>
                <h2>${escapeHtml(sl('knowledgeTitle'))}</h2>
                <p>${escapeHtml(sl('knowledgeBody'))}</p>
              </div>
              <button type="button" data-operator-action="settings">${lang() === 'zh' ? '打开设置' : 'Settings'}</button>
            </div>
            <div class="heytea-guide-toolbar">
              <button type="button" data-operator-action="start-sync">${lang() === 'zh' ? '启动全平台 1小时同步' : 'Start all-platform 1h sync'}</button>
              <button type="button" data-operator-action="stop-sync">${lang() === 'zh' ? '停止同步' : 'Stop sync'}</button>
              <button type="button" data-operator-action="production-check">${lang() === 'zh' ? '生产检查' : 'Production check'}</button>
              <button type="button" data-operator-action="download-support">${lang() === 'zh' ? '导出支持包' : 'Download support pack'}</button>
            </div>
            <div class="heytea-guide-grid">
              <section>
                <h3>${lang() === 'zh' ? '当前运行状态' : 'Runtime Status'}</h3>
                <ul>
                  <li>${lang() === 'zh' ? '门店注册表' : 'Store registry'}: ${escapeHtml(String(status.store_count || 0))}</li>
                  <li>${lang() === 'zh' ? '任务模板' : 'Task templates'}: ${escapeHtml(String(taskNames.length || 0))}</li>
                  <li>${lang() === 'zh' ? '同步监控' : 'Sync monitor'}: ${status.monitor?.running ? (lang() === 'zh' ? '运行中' : 'running') : (lang() === 'zh' ? '未运行' : 'stopped')}</li>
                  <li>${lang() === 'zh' ? '同步间隔' : 'Sync interval'}: ${escapeHtml(String(settings.processing?.sync_interval_seconds || status.monitor?.interval_seconds || 3600))}s</li>
                  <li>${lang() === 'zh' ? '真实任务并发' : 'Real-task concurrency'}: ${escapeHtml(String(settings.processing?.real_concurrency || 1))}</li>
                </ul>
              </section>
              <section>
                <h3>${lang() === 'zh' ? '标准操作流程' : 'Standard Operating Procedure'}</h3>
                <ol>
                  <li>${lang() === 'zh' ? '在设置页确认模型 Base URL、API Key、导出目录、断点目录。' : 'Confirm model Base URL, API key, export directory and checkpoint path in Settings.'}</li>
                  <li>${lang() === 'zh' ? '先运行生产检查，修复高风险项后再启动真实采集。' : 'Run Production Check first; fix high-risk items before real collection.'}</li>
                  <li>${lang() === 'zh' ? '使用近7天或近30天范围，后台按平台账号锁串行执行真实浏览器任务。' : 'Use last 7 or 30 days; real browser jobs run under platform/account locks.'}</li>
                  <li>${lang() === 'zh' ? '任务完成后查看评论工作台、质量报告、失败门店和重试建议。' : 'Review workbench, quality report, failed stores and retry guidance after completion.'}</li>
                </ol>
              </section>
              <section>
                <h3>${lang() === 'zh' ? '异常处理规则' : 'Exception Handling'}</h3>
                <ul>
                  <li>${lang() === 'zh' ? '验证码/二次验证：触发人工门，暂停自动化，不绕过验证码。' : 'CAPTCHA/MFA: trigger human gate; pause automation; never bypass verification.'}</li>
                  <li>${lang() === 'zh' ? '登录态失效：重新登录对应平台后从 checkpoint 续跑。' : 'Expired session: re-login and resume from checkpoint.'}</li>
                  <li>${lang() === 'zh' ? '订单详情为空：检查详情弹窗/API 字段映射，再按失败订单重试。' : 'Missing order details: inspect detail modal/API mapping and retry failed order IDs.'}</li>
                  <li>${lang() === 'zh' ? '图片为空：确认提取的是评论证据图，不是用户头像。' : 'Missing images: verify evidence-image selectors, not customer avatars.'}</li>
                  <li>${lang() === 'zh' ? '页面结构变化：优先更新平台执行器选择器，再启用视觉导航兜底。' : 'Layout change: update platform executor selectors first, then use visual navigation fallback.'}</li>
                </ul>
              </section>
              <section>
                <h3>${lang() === 'zh' ? '生产检查结果' : 'Production Check'}</h3>
                <ul>${checkRows || `<li>${lang() === 'zh' ? '暂无检查结果。' : 'No checks returned.'}</li>`}</ul>
              </section>
            </div>
            <section class="heytea-guide-section">
              <h3>${lang() === 'zh' ? '平台实时同步能力' : 'Platform Sync Capability'}</h3>
              <div class="heytea-guide-table-wrap"><table class="heytea-guide-table"><thead><tr><th>${lang() === 'zh' ? '平台' : 'Platform'}</th><th>Executor</th><th>${lang() === 'zh' ? '订单详情' : 'Order Details'}</th><th>${lang() === 'zh' ? '图片URL' : 'Image URLs'}</th><th>${lang() === 'zh' ? '入口类型' : 'Entry'}</th><th>${lang() === 'zh' ? '任务模板' : 'Template'}</th><th>${lang() === 'zh' ? '最近评论' : 'Latest Reviews'}</th><th>${lang() === 'zh' ? '状态' : 'State'}</th></tr></thead><tbody>${platformRows || ''}</tbody></table></div>
            </section>
            <section class="heytea-guide-section">
              <h3>${lang() === 'zh' ? '最近失败与重试建议' : 'Recent Failures & Retry Guidance'}</h3>
              <ul>${failRows}</ul>
              <p>${lang() === 'zh' ? '点击平台矩阵中的“诊断”可获取实时 AI 处置建议；若模型不可用，系统返回本地规则建议。' : 'Use Diagnose in Platform Matrix for real-time AI remediation; local rules are returned when model APIs are unavailable.'}</p>
            </section>
            <pre class="heytea-settings-output" id="heytea-production-output"></pre>
          </div>`;
        main.querySelectorAll('[data-operator-action]').forEach(button => button.addEventListener('click', async event => {
          event.preventDefault();
          event.stopPropagation();
          const action = button.dataset.operatorAction;
          const output = document.getElementById('heytea-production-output');
          const writeOutput = value => { if (output) output.textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2); };
          try {
            if (action === 'settings') { location.href = '/stitch-static/safety_audit_global/code.html?view=settings'; return; }
            if (action === 'download-support') { await exportVisible(); return; }
            if (action === 'production-check') {
              writeOutput(lang() === 'zh' ? '正在运行生产检查...' : 'Running production check...');
              const result = await apiJson('/api/unified/production-check');
              writeOutput(result);
              return;
            }
            if (action === 'start-sync') {
              writeOutput(lang() === 'zh' ? '正在启动全平台同步...' : 'Starting all-platform sync...');
              const intervalSeconds = await getSyncIntervalSeconds();
              const result = await apiJson('/api/unified/monitor/start', { method: 'POST', body: JSON.stringify({ days: selectedDays(), dry_run: false, interval_seconds: intervalSeconds }) });
              writeOutput(result);
              return;
            }
            if (action === 'stop-sync') {
              const result = await apiJson('/api/unified/monitor/stop', { method: 'POST', body: '{}' });
              writeOutput(result);
            }
          } catch (error) {
            writeOutput(String(error.message || error));
          }
        }));
      }
      return;
    }
    if (view !== 'settings') return;
    const main = document.querySelector('main');
    if (!main) return;
    let payload;
    try { payload = await apiJson('/api/unified/settings'); }
    catch (error) { main.innerHTML = `<div class="heytea-settings-shell">Settings API unavailable: ${escapeHtml(error.message || error)}</div>`; return; }
    window.__heyteaSettings = payload.settings;
    const activeTab = forceTab || sessionStorage.getItem('heytea-settings-tab') || 'api';
    main.innerHTML = `<div class="heytea-settings-shell"><div class="heytea-settings-title"><span class="material-symbols-outlined">settings</span><div><h2>${escapeHtml(sl('title'))}</h2><p>${escapeHtml(sl('subtitle'))}</p></div><button type="button" data-settings-close="true">×</button></div>${renderSettingsTabs(activeTab)}<div class="heytea-settings-content">${renderSettingsContent(payload.settings, activeTab)}</div><div class="heytea-settings-footer"><button type="button" data-settings-action="import">${escapeHtml(sl('import'))}</button><button type="button" data-settings-action="export">${escapeHtml(sl('exportConfig'))}</button><button type="button" data-settings-action="reset">${escapeHtml(sl('reset'))}</button><span></span><button type="button" data-settings-close="true">${escapeHtml(sl('cancel'))}</button><button type="button" class="heytea-settings-primary" data-settings-action="save">${escapeHtml(sl('save'))}</button><input type="file" accept="application/json" id="heytea-settings-import" hidden></div></div>`;
  }
  async function handleSettingsAction(event) {
    const tab = event.target.closest('[data-settings-tab]');
    if (tab) {
      sessionStorage.setItem('heytea-settings-tab', tab.dataset.settingsTab);
      await renderSettingsPage(tab.dataset.settingsTab);
      return;
    }
    const close = event.target.closest('[data-settings-close]');
    if (close) {
      location.href = '/stitch-static/safety_audit_global/code.html';
      return;
    }
    const actionEl = event.target.closest('[data-settings-action]');
    const action = actionEl?.dataset.settingsAction;
    if (!action) return;
    const root = document.querySelector('.heytea-settings-shell');
    if (action === 'browse-folder') {
      const targetPath = actionEl?.dataset.targetSettingPath || '';
      if (!targetPath) return;
      await showFolderPicker(targetPath);
      return;
    }
    if (action === 'export') {
      download('heytea-unified-settings.json', JSON.stringify(window.__heyteaSettings || {}, null, 2), 'application/json;charset=utf-8');
      return;
    }
    if (action === 'import') {
      document.getElementById('heytea-settings-import')?.click();
      return;
    }
    if (action === 'reset') {
      if (!confirm(lang() === 'zh' ? '\u786e\u8ba4\u91cd\u7f6e\u4e3a\u9ed8\u8ba4\u8bbe\u7f6e\uff1f' : 'Reset to default settings?')) return;
      await apiJson('/api/unified/settings', { method: 'POST', body: JSON.stringify({ __reset: true }) });
      await renderSettingsPage();
      notify(lang() === 'zh' ? '\u5df2\u91cd\u8f7d\u9ed8\u8ba4\u8bbe\u7f6e' : 'Defaults reloaded');
      return;
    }
    if (action === 'production-check') {
      const output = document.getElementById('heytea-production-output');
      if (output) output.textContent = 'Running production check...';
      const result = await apiJson('/api/unified/production-check');
      if (output) output.textContent = JSON.stringify(result.production_check, null, 2);
      notify(result.ok ? 'Production check passed' : 'Production check found risks');
      return;
    }
    if (action === 'model-smoke') {
      const output = document.getElementById('heytea-model-output');
      if (output) output.textContent = lang() === 'zh' ? '\u6b63\u5728\u6d4b\u8bd5\u4e3b\u7528\u6a21\u578b...' : 'Testing active model...';
      const activeProvider = document.querySelector('[data-setting-path="api.active_provider"]')?.value || '';
      const result = await apiJson('/api/unified/model-smoke', { method: 'POST', body: JSON.stringify({ provider: activeProvider }) });
      if (output) output.textContent = JSON.stringify(result.result, null, 2);
      notify(result.ok ? (lang() === 'zh' ? '\u6a21\u578b\u8fde\u901a\u6b63\u5e38' : 'Model smoke passed') : (lang() === 'zh' ? '\u6a21\u578b\u8fde\u901a\u5931\u8d25' : 'Model smoke failed'));
      return;
    }
    if (action === 'save') {
      try {
        const patch = collectSettingsPatch(root);
        const result = await apiJson('/api/unified/settings', { method: 'POST', body: JSON.stringify(patch) });
        window.__heyteaSettings = result.settings;
        const nextLang = getPath(patch, 'appearance.language');
        const nextTz = getPath(patch, 'appearance.timezone');
        if (nextLang) localStorage.setItem('heytea_lang', nextLang);
        if (nextTz) localStorage.setItem('heytea_timezone', nextTz);
        normalizeLayout(); normalizeHeader(); startClock(); applyLanguage();
        await renderSettingsPage();
        notify(lang() === 'zh' ? '\u8bbe\u7f6e\u5df2\u4fdd\u5b58' : 'Settings saved');
      } catch (error) {
        showModal('Settings Save Error', String(error.message || error));
      }
    }
  }
  function initSettingsImport() {
    document.addEventListener('change', async event => {
      const input = event.target.closest('#heytea-settings-import');
      if (!input || !input.files?.[0]) return;
      const text = await input.files[0].text();
      try {
        const data = JSON.parse(text);
        const result = await apiJson('/api/unified/settings', { method: 'POST', body: JSON.stringify(data) });
        window.__heyteaSettings = result.settings;
        await renderSettingsPage();
        notify(lang() === 'zh' ? '\u914d\u7f6e\u5df2\u5bfc\u5165' : 'Settings imported');
      } catch (error) {
        showModal('Import Error', String(error.message || error));
      }
    });
  }
  function capabilityLine(label, ok) {
    return `<li class="flex items-center justify-between gap-2 ${ok ? '' : 'opacity-50'}"><span class="text-secondary truncate">${escapeHtml(translatePhrase(label))}</span><span class="material-symbols-outlined ${ok ? 'text-primary' : 'text-outline'} shrink-0" style="font-size: 16px;">${ok ? 'check_circle' : 'cancel'}</span></li>`;
  }
  function patchLegacyTimestampNodes(values) {
    if (!Array.isArray(values) || !values.length) return;
    let index = 0;
    Array.from(document.querySelectorAll('main p, main span, main td, main div')).forEach(node => {
      if (index >= values.length) return;
      if (node.children.length) return;
      const text = cleanText(node);
      if (!text) return;
      if (/^20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}(:\d{2})?(\.\d+)?(\s*UTC|\s*Z)?$/i.test(text)) {
        node.textContent = values[index];
        index += 1;
      }
    });
  }
  function applyQualityFocus(panel) {
    const focus = new URLSearchParams(location.search).get('focus');
    if (focus !== 'ai' || !panel) return;
    const alreadyFocused = sessionStorage.getItem('heytea_quality_focus_applied') === '1';
    const target = panel.querySelector('[data-quality-focus-target="ai"]') || panel;
    if (!alreadyFocused) {
      target.classList.add('ring-2', 'ring-primary');
      setTimeout(() => target.classList.remove('ring-2', 'ring-primary'), 1800);
      sessionStorage.setItem('heytea_quality_focus_applied', '1');
    }
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  async function initQualityReportPage() {
    if (pageByPath() !== 'quality_report') return;
    const renderSeq = nextQualityRenderSeq();
    try {
      const days = selectedDays();
      const requestedQualityPlatform = localStorage.getItem('heytea_quality_platform') || '';
      const requestedQualityPlatformParam = requestedQualityPlatform
        ? `&platform=${encodeURIComponent(requestedQualityPlatform)}`
        : '';
      const qualityTimeoutMs = 3200;
      const main = document.querySelector('main');
      if (!main) return;
      let panel = document.getElementById('heytea-quality-extended');
      if (!panel) {
        panel = document.createElement('section');
        panel.id = 'heytea-quality-extended';
        panel.className = 'space-y-4';
        panel.innerHTML = `<div class="border border-outline-variant p-3 text-secondary text-body-sm">${escapeHtml(lang() === 'zh' ? '正在加载质量分析...' : 'Loading quality analysis...')}</div>`;
        main.appendChild(panel);
      }
      panel.setAttribute('data-quality-focus-target', 'ai');
      applyQualityFocus(panel);
      const endpointErrors = [];
      const composite = await Promise.race([
        apiJsonSoft(`/api/unified/quality-report?days=${days}&limit=1600${requestedQualityPlatformParam}`, null),
        new Promise(resolve => setTimeout(() => resolve({ ok: false, error: `quality-report timeout ${qualityTimeoutMs}ms`, data: null }), qualityTimeoutMs)),
      ]);
      if (!isActiveQualityRender(renderSeq)) return;
      let status = {};
      let reviews = [];
      let insight = null;
      let knowledgeEntries = [];
      let settingsPayload = {};
      let qualityMetrics = null;
      let lastUpdated = '';
      if (composite.ok && composite.data?.ok) {
        status = composite.data.status || {};
        reviews = dedupeReviewRecords(Array.isArray(composite.data.reviews?.reviews) ? composite.data.reviews.reviews : []);
        insight = composite.data.insight || null;
        knowledgeEntries = Array.isArray(composite.data.knowledge?.entries) ? composite.data.knowledge.entries : [];
        settingsPayload = composite.data.settings || {};
        qualityMetrics = composite.data.metrics_quality || null;
        lastUpdated = String(composite.data.last_updated || '');
      } else {
        if (!composite.ok) endpointErrors.push(`quality-report: ${composite.error}`);
        const [statusRes, reviewsRes, insightRes, knowledgeRes, settingsRes] = await Promise.all([
          apiJsonSoft('/api/unified/status', { now: new Date().toISOString(), coordinator: { history: [] }, platforms: {} }),
          apiJsonSoft(`/api/unified/reviews?days=${days}&limit=500${requestedQualityPlatformParam}`, { reviews: [] }),
          apiJsonSoft(`/api/unified/insight?days=${days}&limit=1600${requestedQualityPlatformParam}`, null),
          apiJsonSoft('/api/unified/knowledge?limit=30', { entries: [] }),
          apiJsonSoft('/api/unified/settings', { settings: {} }),
        ]);
        if (!isActiveQualityRender(renderSeq)) return;
        if (!statusRes.ok) endpointErrors.push(`status: ${statusRes.error}`);
        if (!reviewsRes.ok) endpointErrors.push(`reviews: ${reviewsRes.error}`);
        if (!insightRes.ok) endpointErrors.push(`insight: ${insightRes.error}`);
        if (!knowledgeRes.ok) endpointErrors.push(`knowledge: ${knowledgeRes.error}`);
        if (!settingsRes.ok) endpointErrors.push(`settings: ${settingsRes.error}`);
        status = statusRes.data || {};
        reviews = dedupeReviewRecords(Array.isArray(reviewsRes.data?.reviews) ? reviewsRes.data.reviews : []);
        insight = insightRes.data || null;
        knowledgeEntries = Array.isArray(knowledgeRes.data?.entries) ? knowledgeRes.data.entries : [];
        settingsPayload = settingsRes.data || {};
      }
      const platformKeysFromStatus = Object.keys(status.platforms || {}).map(canonicalUiPlatform).filter(Boolean);
      const platformKeysFromReviews = reviews.map(item => canonicalUiPlatform(item.platform || '')).filter(Boolean);
      const availableQualityPlatforms = Array.from(new Set([...platformKeysFromStatus, ...platformKeysFromReviews])).sort();
      let selectedQualityPlatform = requestedQualityPlatform;
      if (selectedQualityPlatform && !availableQualityPlatforms.includes(selectedQualityPlatform)) selectedQualityPlatform = '';
      const selectedKeywordMode = localStorage.getItem('heytea_quality_keyword_mode') || 'all';
      const selectedQualityChart = localStorage.getItem('heytea_quality_chart_view') || 'trend';
      const filteredReviews = selectedQualityPlatform
        ? reviews.filter(item => canonicalUiPlatform(item.platform || '') === selectedQualityPlatform)
        : reviews;
      if (!isActiveQualityRender(renderSeq)) return;
      insight = buildInsightFallbackFromReviews(filteredReviews, days, selectedKeywordMode);
      const fallbackMetrics = computeQualityMetricsLocal(filteredReviews, status.coordinator?.history || [], days);
      const metrics = fallbackMetrics;
      const cards = Array.from(document.querySelectorAll('main .font-display-lg'));
      if (cards[0]) cards[0].textContent = `${Number(metrics.field_completion_rate || 0).toFixed(1)}%`;
      if (cards[1]) cards[1].textContent = `${Number(metrics.detail_coverage || 0).toFixed(1)}%`;
      if (cards[2]) cards[2].textContent = `${Number(metrics.image_coverage || 0).toFixed(1)}%`;
      if (cards[3]) cards[3].textContent = `${Number(metrics.duplicate_rate || 0).toFixed(2)}%`;
      if (cards[4]) cards[4].textContent = Number(metrics.out_of_bounds_count || 0).toLocaleString();
      if (cards[5]) cards[5].textContent = Number(metrics.manual_gate_count || 0).toLocaleString();
      if (cards[6]) cards[6].textContent = Number(metrics.total_errors || 0).toLocaleString();
      const topUpdatedNode = document.querySelector('main .text-right .font-data-mono');
      const updatedStamp = formatIsoInZone(lastUpdated || status.now || new Date().toISOString());
      if (topUpdatedNode) topUpdatedNode.textContent = updatedStamp;
      patchLegacyTimestampNodes([`${updatedStamp} ${tz()}`]);

      let ai = insight.ai || {};
      const daily = Array.isArray(insight.series?.daily_volume) ? insight.series.daily_volume : [];
      const lifecycle = Array.isArray(insight.series?.lifecycle) ? insight.series.lifecycle : [];
      const clusters = Array.isArray(insight.series?.clusters) ? insight.series.clusters : [];
      const keywords = Array.isArray(insight.series?.keywords) ? insight.series.keywords : [];
      const platformVolume = Array.isArray(insight.series?.platform_volume) ? insight.series.platform_volume : buildPlatformVolumeLocal(filteredReviews);
      const riskSamples = Array.isArray(insight.series?.risk_samples) ? insight.series.risk_samples.slice(0, 6) : [];
      const notableDetails = buildNotableDetailRows(filteredReviews, 8);
      const productDemand = buildProductDemandLocal(filteredReviews, 8);
      const reviewRows = [...filteredReviews]
        .sort((a, b) => String(b.review_time || '').localeCompare(String(a.review_time || '')))
        .slice(0, 10);
      const appSettings = settingsPayload.settings || settingsPayload || {};
      const apiSettings = appSettings.api || {};
      const activeProvider = String(apiSettings.active_provider || '').trim();
      const providerPool = apiSettings.providers || {};
      const providerCfg = providerPool[activeProvider] || {};
      const qualitySettings = appSettings.quality || {};
      const draftStorageKey = `heytea_quality_draft_${days}_${selectedQualityPlatform || 'all'}_${selectedKeywordMode}`;
      const savedDraft = localStorage.getItem(draftStorageKey) || '';
      const maxTrend = Math.max(1, ...daily.map(item => Number(item.count || 0)));
      const maxPlatform = Math.max(1, ...platformVolume.map(item => Number(item.count || 0)));
      const maxKeyword = Math.max(1, ...keywords.map(item => Number(item.count || 0)));
      const maxCluster = Math.max(1, ...clusters.map(item => Number(item.count || 0)));
      const platformOptions = `<option value="">${escapeHtml(lang() === 'zh' ? '全部平台' : 'All Platforms')}</option>${availableQualityPlatforms.map(platform => `<option value="${escapeHtml(platform)}" ${platform === selectedQualityPlatform ? 'selected' : ''}>${escapeHtml(platformLabel(platform))}</option>`).join('')}`;
      const keywordModeOptions = Object.keys(keywordModeLabels).map(mode => `<option value="${escapeHtml(mode)}" ${mode === selectedKeywordMode ? 'selected' : ''}>${escapeHtml(keywordModeLabel(mode))}</option>`).join('');
      const filteredScopeLabel = `${selectedQualityPlatform ? platformLabel(selectedQualityPlatform) : (lang() === 'zh' ? '全部平台' : 'All Platforms')} · ${keywordModeLabel(selectedKeywordMode)}`;
      const trendRows = daily.map(row => `<tr class="border-b border-outline-variant"><td class="px-2 py-1 font-data-mono text-data-mono">${escapeHtml(String(row.date || '-'))}</td><td class="px-2 py-1 text-right font-data-mono text-data-mono">${Number(row.count || 0)}</td></tr>`).join('') || `<tr><td colspan="2" class="px-2 py-2 text-secondary">${escapeHtml(lang() === 'zh' ? '暂无趋势数据' : 'No trend data')}</td></tr>`;
      const lifecycleRows = lifecycle.map(row => `<tr class="border-b border-outline-variant"><td class="px-2 py-1 text-secondary">${escapeHtml(String(row.stage || '-'))}</td><td class="px-2 py-1 text-right font-data-mono text-data-mono">${Number(row.count || 0)}</td></tr>`).join('') || `<tr><td colspan="2" class="px-2 py-2 text-secondary">${escapeHtml(lang() === 'zh' ? '暂无生命周期数据' : 'No lifecycle data')}</td></tr>`;
      const clusterRows = clusters.map(row => `<li class="flex justify-between gap-2"><span class="text-secondary">${escapeHtml(String(row.cluster || '-'))}</span><span class="font-data-mono text-data-mono">${Number(row.count || 0)}</span></li>`).join('') || `<li class="text-secondary">${escapeHtml(lang() === 'zh' ? '暂无聚类结果' : 'No clusters')}</li>`;
      const sampleRows = riskSamples.map(row => `<li class="border border-outline-variant p-2"><div class="text-secondary text-[11px]">${escapeHtml(String(row.review_time || '-'))} · ${escapeHtml(String(row.platform || '-'))} · ${escapeHtml(String(row.store || '-'))}</div><div class="text-primary text-body-sm mt-1">${escapeHtml(reviewShort(row.translated_review || row.review || '-', 180))}</div></li>`).join('') || `<li class="text-secondary">${escapeHtml(lang() === 'zh' ? '暂无高风险样本' : 'No risk samples')}</li>`;
      const notableRows = notableDetails.map(row => `<li class="border border-outline-variant p-2"><div class="text-secondary text-[11px]">${escapeHtml(String(row.time || '-'))} · ${escapeHtml(String(row.platform || '-'))} · ${escapeHtml(String(row.store || '-'))} · ${escapeHtml(String(row.rating || '-'))}</div><div class="text-primary text-body-sm mt-1">${escapeHtml(reviewShort(row.text || '-', 180))}</div></li>`).join('') || `<li class="text-secondary">${escapeHtml(lang() === 'zh' ? '暂无个性化明细' : 'No notable details')}</li>`;
      const productRows = (title, rows) => `<div><div class="font-label-caps text-label-caps text-secondary mb-1">${escapeHtml(title)}</div>${rows.map(item => `<div class="flex items-center justify-between gap-2 text-body-sm"><span class="text-primary truncate">${escapeHtml(item.name)}</span><span class="font-data-mono text-data-mono">${Number(item.count || 0)}</span></div>`).join('') || `<div class="text-secondary text-body-sm">-</div>`}</div>`;
      const knowledgeRows = knowledgeEntries.map(entry => `<li class="border border-outline-variant p-2"><div class="flex items-center justify-between gap-2"><span class="font-title-sm text-primary truncate">${escapeHtml(entry.name || entry.id || '-')}</span><button type="button" class="text-error text-[11px]" data-kb-remove="${escapeHtml(entry.id || '')}">${escapeHtml(lang() === 'zh' ? '删除' : 'Remove')}</button></div><p class="text-secondary text-[12px] mt-1 line-clamp-2">${escapeHtml(entry.snippet || '-')}</p></li>`).join('') || `<li class="text-secondary">${escapeHtml(lang() === 'zh' ? '知识库为空' : 'Knowledge base is empty')}</li>`;
      const latestRows = reviewRows.map(review => {
        const rating = Number(reviewRating(review) || 0);
        const sentiment = rating > 0 && rating <= 2 ? (lang() === 'zh' ? '高风险' : 'High Risk') : (lang() === 'zh' ? '常规' : 'Normal');
        return `<tr class="border-b border-outline-variant">
          <td class="px-2 py-1 text-secondary">${escapeHtml(String(review.review_time || '-'))}</td>
          <td class="px-2 py-1 text-secondary">${escapeHtml(platformLabel(review.platform || '-'))}</td>
          <td class="px-2 py-1 text-secondary">${escapeHtml(String(review.store || '-'))}</td>
          <td class="px-2 py-1 text-right font-data-mono text-data-mono">${rating ? rating.toFixed(1) : '-'}</td>
          <td class="px-2 py-1 text-right ${rating > 0 && rating <= 2 ? 'text-error' : 'text-primary'}">${escapeHtml(sentiment)}</td>
        </tr>`;
      }).join('') || `<tr><td colspan="5" class="px-2 py-2 text-secondary">${escapeHtml(lang() === 'zh' ? '暂无实时评论' : 'No realtime reviews')}</td></tr>`;
      const endpointWarn = endpointErrors.length
        ? `<div class="border border-[#ff9800] bg-[#fff7e6] text-[#8a4b00] px-3 py-2 text-[12px]">${escapeHtml((lang() === 'zh' ? '接口降级模式：' : 'Degraded API mode: ') + endpointErrors.join(' | '))}</div>`
        : '';

      panel.innerHTML = `
        ${endpointWarn}
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <section class="bg-surface-container-lowest border border-outline p-4 lg:col-span-2 space-y-3">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 class="font-title-sm text-title-sm text-primary">${escapeHtml(lang() === 'zh' ? '实时评论分析与质量报告' : 'Realtime Review Analysis & Quality Report')}</h3>
                <div class="text-[12px] text-secondary">${escapeHtml(filteredScopeLabel)} · ${escapeHtml(lang() === 'zh' ? `当前样本 ${filteredReviews.length}/${reviews.length} 条` : `${filteredReviews.length}/${reviews.length} records`)}</div>
              </div>
              <div class="flex flex-wrap items-center gap-2">
                <select data-quality-platform-filter class="border border-outline-variant bg-surface-container-lowest p-2 text-body-sm">${platformOptions}</select>
                <select data-quality-keyword-mode class="border border-outline-variant bg-surface-container-lowest p-2 text-body-sm">${keywordModeOptions}</select>
                <span class="font-data-mono text-data-mono text-secondary">${escapeHtml(`${days}d`)}</span>
              </div>
            </div>
            <p class="text-primary text-body-sm" data-quality-ai-summary>${escapeHtml(ai.summary || (lang() === 'zh' ? '暂无AI报告' : 'No AI report yet'))}</p>
            <p class="text-secondary text-[12px]" data-quality-ai-findings>${escapeHtml((ai.key_findings || []).join('； '))}</p>
            <p class="text-secondary text-[12px]" data-quality-ai-actions>${escapeHtml((ai.actions || []).join('； '))}</p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div class="border border-outline-variant p-2">
                <h4 class="font-label-caps text-label-caps text-secondary mb-1">${escapeHtml(lang() === 'zh' ? '时间趋势' : 'Time Trend')}</h4>
                <table class="w-full text-body-sm"><tbody>${trendRows}</tbody></table>
              </div>
              <div class="border border-outline-variant p-2">
                <h4 class="font-label-caps text-label-caps text-secondary mb-1">${escapeHtml(lang() === 'zh' ? '生命周期分层' : 'Lifecycle')}</h4>
                <table class="w-full text-body-sm"><tbody>${lifecycleRows}</tbody></table>
              </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div class="border border-outline-variant p-2">
                <h4 class="font-label-caps text-label-caps text-secondary mb-1">${escapeHtml(lang() === 'zh' ? '投诉聚类' : 'Complaint Clusters')}</h4>
                <ul class="space-y-1">${clusterRows}</ul>
              </div>
              <div class="border border-outline-variant p-2">
                <h4 class="font-label-caps text-label-caps text-secondary mb-1">${escapeHtml(lang() === 'zh' ? '重点食安问题' : 'Food Safety Issues')}</h4>
                <p class="text-body-sm text-primary" data-quality-food-safety>${escapeHtml((ai.food_safety_issues || []).join('、') || (lang() === 'zh' ? '暂无' : 'None'))}</p>
                <p class="text-secondary text-[12px] mt-2" data-quality-trend-observation>${escapeHtml(ai.trend_observation || '')}</p>
              </div>
            </div>
            <div class="border border-outline-variant p-2 space-y-2">
              <div class="flex flex-wrap gap-2">
                <button class="px-2 py-1 border border-outline-variant text-body-sm" data-quality-chart="trend">${escapeHtml(lang() === 'zh' ? '趋势' : 'Trend')}</button>
                <button class="px-2 py-1 border border-outline-variant text-body-sm" data-quality-chart="platform">${escapeHtml(lang() === 'zh' ? '平台' : 'Platform')}</button>
                <button class="px-2 py-1 border border-outline-variant text-body-sm" data-quality-chart="keywords">${escapeHtml(lang() === 'zh' ? '业务关键词' : 'Business Keywords')}</button>
                <button class="px-2 py-1 border border-outline-variant text-body-sm" data-quality-chart="clusters">${escapeHtml(lang() === 'zh' ? '聚类' : 'Clusters')}</button>
                <button class="px-2 py-1 border border-outline-variant text-body-sm" data-quality-chart="products">${escapeHtml(lang() === 'zh' ? '产品需求' : 'Product Demand')}</button>
              </div>
              <div data-quality-panel="trend" style="${selectedQualityChart === 'trend' ? '' : 'display:none'}">
                ${daily.map(item => `<div class="flex items-center gap-2 mb-1"><div class="w-28 text-body-sm text-primary">${escapeHtml(String(item.date || '-').slice(5))}</div><div class="flex-1 h-2 bg-surface-container-high"><div class="h-2 bg-primary" style="width:${Math.max(6, Math.round((Number(item.count || 0) / maxTrend) * 100))}%"></div></div><div class="w-12 text-right font-data-mono text-data-mono">${Number(item.count || 0)}</div></div>`).join('') || `<div class="text-secondary">${escapeHtml(lang() === 'zh' ? '暂无趋势数据' : 'No trend data')}</div>`}
              </div>
              <div data-quality-panel="platform" style="${selectedQualityChart === 'platform' ? '' : 'display:none'}">
                ${platformVolume.map(item => `<div class="flex items-center gap-2 mb-1"><div class="w-36 truncate text-body-sm text-primary">${escapeHtml(platformLabel(item.platform || ''))}</div><div class="flex-1 h-2 bg-surface-container-high"><div class="h-2 bg-primary" style="width:${Math.max(6, Math.round((Number(item.count || 0) / maxPlatform) * 100))}%"></div></div><div class="w-12 text-right font-data-mono text-data-mono">${Number(item.count || 0)}</div></div>`).join('') || `<div class="text-secondary">${escapeHtml(lang() === 'zh' ? '暂无平台数据' : 'No platform data')}</div>`}
              </div>
              <div data-quality-panel="keywords" style="${selectedQualityChart === 'keywords' ? '' : 'display:none'}">
                ${keywords.map(item => `<div class="flex items-center gap-2 mb-1"><div class="w-36 truncate text-body-sm text-primary">${escapeHtml(String(item.keyword || ''))}</div><div class="flex-1 h-2 bg-surface-container-high"><div class="h-2 bg-[#ff9800]" style="width:${Math.max(6, Math.round((Number(item.count || 0) / maxKeyword) * 100))}%"></div></div><div class="w-12 text-right font-data-mono text-data-mono">${Number(item.count || 0)}</div></div>`).join('') || `<div class="text-secondary">${escapeHtml(lang() === 'zh' ? '暂无关键词' : 'No keywords')}</div>`}
              </div>
              <div data-quality-panel="clusters" style="${selectedQualityChart === 'clusters' ? '' : 'display:none'}">
                ${clusters.map(item => `<div class="flex items-center gap-2 mb-1"><div class="w-36 truncate text-body-sm text-primary">${escapeHtml(String(item.cluster || ''))}</div><div class="flex-1 h-2 bg-surface-container-high"><div class="h-2 bg-[#8e44ad]" style="width:${Math.max(6, Math.round((Number(item.count || 0) / maxCluster) * 100))}%"></div></div><div class="w-12 text-right font-data-mono text-data-mono">${Number(item.count || 0)}</div></div>`).join('') || `<div class="text-secondary">${escapeHtml(lang() === 'zh' ? '暂无聚类结果' : 'No clusters')}</div>`}
              </div>
              <div data-quality-panel="products" style="${selectedQualityChart === 'products' ? '' : 'display:none'}">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                  ${productRows(lang() === 'zh' ? '高评分关联商品' : 'Most-liked Items', productDemand.liked)}
                  ${productRows(lang() === 'zh' ? '低评分关联商品' : 'Most-complained Items', productDemand.disliked)}
                </div>
              </div>
            </div>
            <div class="border border-outline-variant p-2">
              <h4 class="font-label-caps text-label-caps text-secondary mb-1">${escapeHtml(lang() === 'zh' ? '高风险评论样本' : 'High-risk Samples')}</h4>
              <ul class="space-y-2">${sampleRows}</ul>
            </div>
            <div class="border border-outline-variant p-2">
              <h4 class="font-label-caps text-label-caps text-secondary mb-1">${escapeHtml(lang() === 'zh' ? '个性化/低频但重要明细' : 'Unique Low-frequency Details')}</h4>
              <ul class="space-y-2">${notableRows}</ul>
            </div>
            <div class="border border-outline-variant p-2">
              <h4 class="font-label-caps text-label-caps text-secondary mb-1">${escapeHtml(lang() === 'zh' ? '实时评论分析区' : 'Realtime Review Analysis')}</h4>
              <table class="w-full text-body-sm">
                <thead><tr class="border-b border-outline-variant"><th class="px-2 py-1 text-left">${escapeHtml(lang() === 'zh' ? '时间' : 'Time')}</th><th class="px-2 py-1 text-left">${escapeHtml(lang() === 'zh' ? '平台' : 'Platform')}</th><th class="px-2 py-1 text-left">${escapeHtml(lang() === 'zh' ? '门店' : 'Store')}</th><th class="px-2 py-1 text-right">${escapeHtml(lang() === 'zh' ? '评分' : 'Rating')}</th><th class="px-2 py-1 text-right">${escapeHtml(lang() === 'zh' ? '风险' : 'Risk')}</th></tr></thead>
                <tbody>${latestRows}</tbody>
              </table>
            </div>
          </section>
          <section class="bg-surface-container-lowest border border-outline p-4 space-y-3" data-quality-focus-target="ai">
            <h3 class="font-title-sm text-title-sm text-primary">${escapeHtml(lang() === 'zh' ? '报告构建与模型调试' : 'Report Builder & Model Debug')}</h3>
            <textarea id="heytea-quality-draft" class="w-full border border-outline-variant p-2 text-body-sm" rows="6" placeholder="${escapeHtml(lang() === 'zh' ? '生成/编辑质量报告草稿...' : 'Generate/edit quality report draft...')}">${escapeHtml(savedDraft)}</textarea>
            <div class="flex flex-wrap gap-2">
              <button type="button" class="px-3 py-2 border border-primary text-primary" data-quality-draft="build">${escapeHtml(lang() === 'zh' ? '生成草稿' : 'Build Draft')}</button>
              <button type="button" class="px-3 py-2 border border-outline-variant text-primary" data-quality-draft="export">${escapeHtml(lang() === 'zh' ? '导出草稿' : 'Export Draft')}</button>
              <button type="button" class="px-3 py-2 border border-outline-variant text-primary" data-quality-draft="refresh">${escapeHtml(lang() === 'zh' ? '刷新分析' : 'Refresh')}</button>
            </div>
            <div class="border border-outline-variant p-2 bg-surface-container-low">
              <div class="font-label-caps text-label-caps text-secondary mb-1">${escapeHtml(lang() === 'zh' ? 'AI模型调试' : 'AI Model Debug')}</div>
              <div class="text-body-sm text-secondary">${escapeHtml((providerCfg.label || activeProvider || 'N/A'))} · ${escapeHtml(String(providerCfg.model || '-'))}</div>
              <div class="text-[12px] text-secondary break-all">${escapeHtml(String(providerCfg.base_url || '-'))}</div>
              <button type="button" class="mt-2 px-3 py-2 border border-outline-variant text-primary" data-quality-model-smoke="run">${escapeHtml(lang() === 'zh' ? '模型连通测试' : 'Run Model Smoke')}</button>
              <pre id="heytea-quality-model-output" class="mt-2 text-[11px] border border-outline-variant p-2 max-h-[180px] overflow-auto">${escapeHtml(lang() === 'zh' ? '等待测试...' : 'Waiting...')}</pre>
            </div>
            <div class="border border-outline-variant p-2 bg-surface-container-low space-y-2">
              <div class="font-label-caps text-label-caps text-secondary">${escapeHtml(lang() === 'zh' ? '质量阈值（自动保存）' : 'Quality Thresholds (Auto-save)')}</div>
              <label class="block text-body-sm text-secondary">${escapeHtml(lang() === 'zh' ? '字段完整率下限' : 'Min field completeness')}
                <input class="w-full border border-outline-variant p-2 text-body-sm" type="number" min="0" max="1" step="0.01" data-quality-setting-path="quality.min_field_completeness" value="${escapeHtml(String(qualitySettings.min_field_completeness ?? 0.95))}" />
              </label>
              <label class="block text-body-sm text-secondary">${escapeHtml(lang() === 'zh' ? '订单详情覆盖率下限' : 'Min order detail coverage')}
                <input class="w-full border border-outline-variant p-2 text-body-sm" type="number" min="0" max="1" step="0.01" data-quality-setting-path="quality.min_detail_coverage" value="${escapeHtml(String(qualitySettings.min_detail_coverage ?? 0.9))}" />
              </label>
              <label class="block text-body-sm text-secondary">${escapeHtml(lang() === 'zh' ? '重复率上限' : 'Max duplicate rate')}
                <input class="w-full border border-outline-variant p-2 text-body-sm" type="number" min="0" max="1" step="0.001" data-quality-setting-path="quality.max_duplicate_rate" value="${escapeHtml(String(qualitySettings.max_duplicate_rate ?? 0.01))}" />
              </label>
              <pre id="heytea-quality-save-output" class="text-[11px] border border-outline-variant p-2">${escapeHtml(lang() === 'zh' ? '修改后自动保存到后端配置。' : 'Changes are persisted to backend settings automatically.')}</pre>
            </div>
            <h3 class="font-title-sm text-title-sm text-primary">${escapeHtml(lang() === 'zh' ? '知识库（报告风格/规则）' : 'Knowledge Base (Style & Rules)')}</h3>
            <textarea id="heytea-kb-content" class="w-full border border-outline-variant p-2 text-body-sm" rows="5" placeholder="${escapeHtml(lang() === 'zh' ? '粘贴历史质量报告、规则、术语要求...' : 'Paste previous reports, rules, terminology...')}"></textarea>
            <div class="flex flex-wrap gap-2">
              <input id="heytea-kb-name" class="border border-outline-variant p-2 text-body-sm flex-1 min-w-[120px]" placeholder="${escapeHtml(lang() === 'zh' ? '知识条目名称' : 'Entry name')}" />
              <button type="button" class="px-3 py-2 border border-primary text-primary" data-kb-add="manual">${escapeHtml(lang() === 'zh' ? '添加文本' : 'Add Text')}</button>
            </div>
            <div class="flex items-center gap-2">
              <input id="heytea-kb-file" type="file" accept=".txt,.md,.json,.csv,.xlsx,.xlsm,.docx,.pdf" class="text-body-sm" />
              <button type="button" class="px-3 py-2 border border-outline-variant text-primary" data-kb-add="file">${escapeHtml(lang() === 'zh' ? '上传文件' : 'Upload File')}</button>
            </div>
            <pre id="heytea-kb-upload-status" class="text-[11px] border border-outline-variant p-2">${escapeHtml(lang() === 'zh' ? '支持 TXT/MD/JSON/CSV/XLSX/DOCX/PDF，上传后立即写入知识库并参与报告生成。' : 'Supports TXT/MD/JSON/CSV/XLSX/DOCX/PDF. Uploads are persisted immediately and used in report generation.')}</pre>
            <ul class="space-y-2 max-h-[320px] overflow-auto">${knowledgeRows}</ul>
          </section>
        </div>`;
      panel.querySelectorAll('[data-quality-chart]').forEach(button => button.addEventListener('click', () => {
        const view = button.dataset.qualityChart;
        localStorage.setItem('heytea_quality_chart_view', String(view || 'trend'));
        panel.querySelectorAll('[data-quality-panel]').forEach(section => {
          section.style.display = section.dataset.qualityPanel === view ? '' : 'none';
        });
      }));
      apiJsonSoft(`/api/unified/insight?days=${days}&limit=1600${requestedQualityPlatformParam}`, null).then(result => {
        if (!isActiveQualityRender(renderSeq) || !result.ok || !result.data?.ok) return;
        const serverAi = result.data.ai || {};
        ai = serverAi;
        const summary = panel.querySelector('[data-quality-ai-summary]');
        const findings = panel.querySelector('[data-quality-ai-findings]');
        const actions = panel.querySelector('[data-quality-ai-actions]');
        const foodSafety = panel.querySelector('[data-quality-food-safety]');
        const trend = panel.querySelector('[data-quality-trend-observation]');
        if (summary) summary.textContent = String(serverAi.summary || summary.textContent || '');
        if (findings) findings.textContent = String((serverAi.key_findings || []).join('； ') || findings.textContent || '');
        if (actions) actions.textContent = String((serverAi.actions || []).join('； ') || actions.textContent || '');
        if (foodSafety) foodSafety.textContent = String((serverAi.food_safety_issues || []).join('、') || (lang() === 'zh' ? '暂无' : 'None'));
        if (trend) trend.textContent = String(serverAi.trend_observation || trend.textContent || '');
      }).catch(() => {});
      panel.querySelector('[data-quality-platform-filter]')?.addEventListener('change', async event => {
        localStorage.setItem('heytea_quality_platform', String(event.target.value || ''));
        panel.innerHTML = `<div class="border border-outline-variant p-3 text-secondary text-body-sm">${escapeHtml(lang() === 'zh' ? '正在按平台刷新分析...' : 'Refreshing analysis by platform...')}</div>`;
        await initQualityReportPage();
      });
      panel.querySelector('[data-quality-keyword-mode]')?.addEventListener('change', async event => {
        localStorage.setItem('heytea_quality_keyword_mode', String(event.target.value || 'all'));
        panel.innerHTML = `<div class="border border-outline-variant p-3 text-secondary text-body-sm">${escapeHtml(lang() === 'zh' ? '正在按主题刷新分析...' : 'Refreshing analysis by topic...')}</div>`;
        await initQualityReportPage();
      });
      panel.querySelector('#heytea-quality-draft')?.addEventListener('input', event => {
        localStorage.setItem(draftStorageKey, String(event.target.value || ''));
      });
      let qualitySaveTimer = null;
      const saveQualitySettings = async () => {
        const output = panel.querySelector('#heytea-quality-save-output');
        const patch = {};
        panel.querySelectorAll('[data-quality-setting-path]').forEach(input => {
          const value = input.type === 'number' ? Number(input.value) : input.value;
          setPath(patch, input.dataset.qualitySettingPath, value);
        });
        if (output) output.textContent = lang() === 'zh' ? '正在保存质量配置...' : 'Saving quality settings...';
        const result = await apiJson('/api/unified/settings', { method: 'POST', body: JSON.stringify(patch) });
        window.__heyteaSettings = result.settings;
        if (output) output.textContent = `${lang() === 'zh' ? '已自动保存' : 'Auto-saved'} · ${formatIsoInZone(new Date().toISOString())}`;
      };
      panel.querySelectorAll('[data-quality-setting-path]').forEach(input => {
        const onSave = () => {
          clearTimeout(qualitySaveTimer);
          qualitySaveTimer = setTimeout(() => saveQualitySettings().catch(error => {
            const output = panel.querySelector('#heytea-quality-save-output');
            if (output) output.textContent = `${lang() === 'zh' ? '保存失败' : 'Save failed'}: ${error.message || error}`;
          }), 700);
        };
        input.addEventListener('input', onSave);
        input.addEventListener('change', () => {
          clearTimeout(qualitySaveTimer);
          saveQualitySettings().catch(error => {
            const output = panel.querySelector('#heytea-quality-save-output');
            if (output) output.textContent = `${lang() === 'zh' ? '保存失败' : 'Save failed'}: ${error.message || error}`;
          });
        });
      });
      panel.querySelector('[data-quality-draft="build"]')?.addEventListener('click', () => {
        const draft = panel.querySelector('#heytea-quality-draft');
        if (!draft) return;
        const findingText = (ai.key_findings || []).join('\n- ');
        const actionText = (ai.actions || []).join('\n- ');
        const keywordText = keywords.slice(0, 8).map(item => `${item.keyword} (${item.count})`).join(', ');
        const content = lang() === 'zh'
          ? `# 质量报告草稿（${days}天）\n\n## 分析范围\n- 平台/主题：${filteredScopeLabel}\n- 评论样本：${filteredReviews.length}/${reviews.length}\n\n## 总览\n- 风险评论：${Number(insight.metrics?.risk_count || 0)}\n- 字段完整率：${Number(metrics.field_completion_rate || 0).toFixed(1)}%\n- 订单详情覆盖率：${Number(metrics.detail_coverage || 0).toFixed(1)}%\n\n## AI解读\n${ai.summary || '暂无'}\n\n## 关键发现\n- ${findingText || '暂无'}\n\n## 业务关键词\n${keywordText || '暂无'}\n\n## 个性化明细\n${notableDetails.slice(0, 5).map(item => `- ${item.store}：${reviewShort(item.text, 120)}`).join('\n') || '- 暂无'}\n\n## 改进建议\n- ${actionText || '暂无'}\n`
          : `# Quality Report Draft (${days}d)\n\n## Scope\n- Platform/topic: ${filteredScopeLabel}\n- Review sample: ${filteredReviews.length}/${reviews.length}\n\n## Overview\n- Risk reviews: ${Number(insight.metrics?.risk_count || 0)}\n- Field completion: ${Number(metrics.field_completion_rate || 0).toFixed(1)}%\n- Order detail coverage: ${Number(metrics.detail_coverage || 0).toFixed(1)}%\n\n## AI Insight\n${ai.summary || 'N/A'}\n\n## Key Findings\n- ${findingText || 'N/A'}\n\n## Business Keywords\n${keywordText || 'N/A'}\n\n## Unique Details\n${notableDetails.slice(0, 5).map(item => `- ${item.store}: ${reviewShort(item.text, 120)}`).join('\n') || '- N/A'}\n\n## Actions\n- ${actionText || 'N/A'}\n`;
        draft.value = content;
        localStorage.setItem(draftStorageKey, content);
      });
      panel.querySelector('[data-quality-draft="export"]')?.addEventListener('click', () => {
        const draft = panel.querySelector('#heytea-quality-draft');
        const content = String(draft?.value || '').trim();
        if (!content) {
          notify(lang() === 'zh' ? '草稿为空，无法导出' : 'Draft is empty');
          return;
        }
        const stamp = new Date().toISOString().replace(/[-:TZ]/g, '').slice(0, 14);
        download(`quality_report_draft_${stamp}.md`, content, 'text/markdown;charset=utf-8');
      });
      panel.querySelector('[data-quality-draft="refresh"]')?.addEventListener('click', async () => {
        await initQualityReportPage();
      });
      panel.querySelector('[data-quality-model-smoke="run"]')?.addEventListener('click', async () => {
        const output = panel.querySelector('#heytea-quality-model-output');
        try {
          if (output) output.textContent = lang() === 'zh' ? '测试中...' : 'Running...';
          const result = await apiJson('/api/unified/model-smoke', { method: 'POST', body: JSON.stringify({ provider: activeProvider }) });
          if (output) output.textContent = JSON.stringify(result.result || result, null, 2);
        } catch (error) {
          if (output) output.textContent = `${lang() === 'zh' ? '模型测试失败' : 'Model smoke failed'}: ${error.message || error}`;
        }
      });

      panel.querySelector('[data-kb-add="manual"]')?.addEventListener('click', async () => {
        const name = String(panel.querySelector('#heytea-kb-name')?.value || '').trim() || `note_${Date.now()}`;
        const content = String(panel.querySelector('#heytea-kb-content')?.value || '').trim();
        if (!content) {
          notify(lang() === 'zh' ? '请先输入知识内容' : 'Please input knowledge content first');
          return;
        }
        try {
          const result = await apiJson('/api/unified/knowledge', { method: 'POST', body: JSON.stringify({ name, content, source_type: 'manual' }) });
          if (!result.ok) throw new Error(result.error || 'knowledge_save_failed');
          notify(lang() === 'zh' ? '知识库已更新' : 'Knowledge base updated');
          await initQualityReportPage();
        } catch (error) {
          notify(`${lang() === 'zh' ? '知识库保存失败：' : 'Knowledge save failed: '}${error.message || error}`);
        }
      });
      panel.querySelector('[data-kb-add="file"]')?.addEventListener('click', async () => {
        const file = panel.querySelector('#heytea-kb-file')?.files?.[0];
        const status = panel.querySelector('#heytea-kb-upload-status');
        if (!file) {
          notify(lang() === 'zh' ? '请选择文件' : 'Please select a file');
          return;
        }
        try {
          if (status) status.textContent = `${lang() === 'zh' ? '正在上传并解析' : 'Uploading and parsing'}: ${file.name}`;
          const content_base64 = arrayBufferToBase64(await file.arrayBuffer());
          const result = await apiJson('/api/unified/knowledge/upload', { method: 'POST', body: JSON.stringify({ filename: file.name, content_base64 }) });
          if (!result.ok) throw new Error(result.error || 'upload_failed');
          if (status) status.textContent = `${lang() === 'zh' ? '上传成功' : 'Upload saved'}: ${file.name} · ${Number(result.chars || 0)} chars`;
          notify(lang() === 'zh' ? '文件已加入知识库' : 'File imported to knowledge base');
          await initQualityReportPage();
        } catch (error) {
          if (status) status.textContent = `${lang() === 'zh' ? '上传失败' : 'Upload failed'}: ${error.message || error}`;
          notify(`${lang() === 'zh' ? '上传失败：' : 'Upload failed: '}${error.message || error}`);
        }
      });
      panel.querySelectorAll('[data-kb-remove]').forEach(button => button.addEventListener('click', async () => {
        const id = button.dataset.kbRemove;
        if (!id) return;
        await apiJson('/api/unified/knowledge/delete', { method: 'POST', body: JSON.stringify({ id }) });
        notify(lang() === 'zh' ? '知识条目已删除' : 'Knowledge entry removed');
        await initQualityReportPage();
      }));
      applyQualityFocus(panel);
      if (endpointErrors.length) {
        const endpointKey = endpointErrors.join('|');
        const previous = sessionStorage.getItem('heytea_quality_endpoint_errors') || '';
        if (endpointKey !== previous) {
          sessionStorage.setItem('heytea_quality_endpoint_errors', endpointKey);
          notify(`${lang() === 'zh' ? '质量页已自动降级，接口异常：' : 'Quality page running in degraded mode: '}${endpointErrors.join(' | ')}`);
        }
      } else {
        sessionStorage.removeItem('heytea_quality_endpoint_errors');
      }
    } catch (error) {
      notify(`Quality report refresh failed: ${error.message || error}`);
    }
  }
  async function initSafetyAuditPage() {
    if (pageByPath() !== 'safety_audit') return;
    try {
      const [payload, status] = await Promise.all([
        apiJson('/api/unified/events?since_id=0'),
        apiJson('/api/unified/status'),
      ]);
      const events = (payload.events || []).slice(-30).reverse();
      const tbody = document.querySelector('main table tbody');
      if (tbody) {
        tbody.innerHTML = events.length
          ? events.map(event => {
              const level = String(event.level || 'info').toLowerCase();
              const badgeCls = level === 'error'
                ? 'bg-error text-on-error'
                : level === 'warning'
                  ? 'bg-[#ff9800] text-primary'
                  : level === 'success'
                    ? 'bg-primary text-on-primary'
                    : 'bg-surface-variant text-primary border border-outline-variant';
              return `<tr class="border-b border-outline-variant hover:bg-surface-bright transition-colors">
                <td class="px-3 py-2 font-data-mono text-data-mono text-primary">${escapeHtml(String(event.id || '-'))}</td>
                <td class="px-3 py-2 text-on-surface-variant font-data-mono text-data-mono">${escapeHtml(formatIsoInZone(event.created_at || ''))}</td>
                <td class="px-3 py-2 text-primary">${escapeHtml(translateDynamicText(event.title || 'Platform event'))}</td>
                <td class="px-3 py-2 text-on-surface-variant">${escapeHtml(translateDynamicText(event.message || '-'))}</td>
                <td class="px-3 py-2"><span class="inline-flex items-center px-2 py-0.5 ${badgeCls} font-label-caps text-[10px] uppercase">${escapeHtml(translateDynamicText(level || 'info'))}</span></td>
              </tr>`;
            }).join('')
          : `<tr><td colspan="5" class="px-3 py-4 text-center text-secondary">${escapeHtml(translateDynamicText('No audit events yet'))}</td></tr>`;
      }
      const humanGateTitle = Array.from(document.querySelectorAll('main h4')).find(node => cleanText(node).toLowerCase().includes('human-gate'));
      const humanGateContainer = humanGateTitle?.parentElement?.nextElementSibling;
      if (humanGateContainer) {
        const gateEvents = events
          .filter(event => /captcha|manual|blocked|forbidden|write|login/i.test(`${event.title || ''} ${event.message || ''}`))
          .slice(0, 3);
        humanGateContainer.innerHTML = gateEvents.length
          ? gateEvents.map(event => {
              const level = String(event.level || 'info').toLowerCase();
              const badgeCls = level === 'error' ? 'bg-error text-on-error' : level === 'warning' ? 'bg-[#ff9800] text-primary' : 'bg-primary text-on-primary';
              const statusText = level === 'error' ? (lang() === 'zh' ? '已中止' : 'ABORTED') : level === 'warning' ? (lang() === 'zh' ? '已验证' : 'VERIFIED') : (lang() === 'zh' ? '已解决' : 'RESOLVED');
              return `<div class="border-l-2 ${level === 'error' ? 'border-error' : level === 'warning' ? 'border-[#ff9800]' : 'border-primary'} pl-3">
                <div class="flex justify-between items-start mb-1 gap-2">
                  <span class="font-data-mono text-[11px] text-secondary">${escapeHtml(formatIsoInZone(event.created_at || ''))}</span>
                  <span class="${badgeCls} font-label-caps text-[9px] px-1.5 py-0.5">${escapeHtml(statusText)}</span>
                </div>
                <h5 class="font-title-sm text-primary mb-1">${escapeHtml(translateDynamicText(event.title || (lang() === 'zh' ? '人工门事件' : 'Human-gate event')))}</h5>
                <p class="font-body-sm text-on-surface-variant">${escapeHtml(translateDynamicText(event.message || '-'))}</p>
              </div>`;
            }).join('')
          : `<div class="text-body-sm text-secondary">${escapeHtml(translateDynamicText('No human-gate events'))}</div>`;
      }
      const exportTitle = Array.from(document.querySelectorAll('main h4')).find(node => cleanText(node).toLowerCase().includes('export activity log'));
      const exportList = exportTitle?.parentElement?.nextElementSibling;
      if (exportList) {
        const exportFiles = (status.exports || []).slice(0, 8);
        exportList.innerHTML = exportFiles.length
          ? exportFiles.map(file => `<li class="p-3">
              <div class="flex justify-between items-center mb-1 gap-2">
                <span class="font-title-sm text-primary">${escapeHtml(translateDynamicText('System Export Job'))}</span>
                <span class="font-data-mono text-[11px] text-secondary">${escapeHtml(formatIsoInZone(file.mtime || ''))}</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-[16px] text-secondary">${String(file.name || '').endsWith('.json') ? 'database' : 'download'}</span>
                <span class="font-body-sm text-on-surface-variant truncate">${escapeHtml(file.name || '-')}</span>
              </div>
            </li>`).join('')
          : `<li class="p-3 text-body-sm text-secondary">${escapeHtml(translateDynamicText('No export records'))}</li>`;
      }
      const fallbackTimes = Array.from({ length: 12 }, (_item, index) => {
        const date = new Date(Date.now() - index * 60_000);
        return formatIsoInZone(date.toISOString());
      });
      const legacyTimes = events.length
        ? events.slice(0, 12).map(event => formatIsoInZone(event.created_at || ''))
        : fallbackTimes;
      patchLegacyTimestampNodes(legacyTimes);
    } catch (error) {
      notify(`Safety audit refresh failed: ${error.message || error}`);
    }
  }
  function platformIconHtml(key, covered) {
    const meta = platformMeta[canonicalUiPlatform(key)] || { short: platformLabel(key), icon: 'apps' };
    return `<div class="w-6 h-6 flex items-center justify-center ${covered ? 'bg-primary text-on-primary' : 'bg-outline-variant text-surface-container-lowest'}" title="${escapeHtml(meta.label)}"><span class="material-symbols-outlined text-[14px]">${meta.icon}</span></div>`;
  }
  function filteredStoreCoverageRows() {
    const state = window.__heyteaStoreCoverage;
    if (!state) return [];
    const country = state.country || '';
    const platform = state.platform || '';
    const jde = (state.jde || '').toLowerCase();
    const query = (state.query || '').toLowerCase();
    return state.stores.filter(store => {
      const platforms = storePlatformKeys(store);
      if (country && normalizeRegionText(String(store.country || '')) !== country) return false;
      if (platform && !platforms.includes(platform)) return false;
      if (jde && !String(store.jde || '').toLowerCase().includes(jde)) return false;
      if (query && !String(store.store_name || '').toLowerCase().includes(query)) return false;
      return true;
    });
  }
  function renderStoreDetail(store) {
    const state = window.__heyteaStoreCoverage;
    const aside = document.querySelector('main aside.w-\\[380px\\], main aside');
    if (!state || !aside || !store) return;
    const platforms = storePlatformKeys(store);
    const capabilities = state.status?.platforms || {};
    const hasPhotos = platforms.some(key => capabilities[key]?.supports_review_images);
    const hasTranslation = platforms.some(key => capabilities[key]?.supports_translation_source);
    const hasOrder = platforms.some(key => capabilities[key]?.supports_order_detail);
    const entries = Object.entries(store.platforms || {}).map(([key, pdata]) => {
      const canonical = canonicalUiPlatform(key);
      const meta = platformMeta[canonical] || { label: platformLabel(key), short: platformLabel(key), icon: 'apps', url: '' };
      const url = platformEntryUrl(canonical, pdata);
      const href = url ? escapeHtml(url) : '#';
      const attrs = url ? 'target="_blank" rel="noopener noreferrer"' : 'data-no-url="true"';
      return `<a class="group flex items-center justify-between p-2 border border-outline-variant hover:border-primary transition-colors bg-surface-container-low gap-2" href="${href}" ${attrs} data-platform-entry="${escapeHtml(canonical)}">
        <div class="flex items-center gap-2 min-w-0"><span class="material-symbols-outlined text-primary shrink-0" style="font-size: 16px;">${meta.icon}</span><span class="font-body-sm text-body-sm text-primary truncate">${escapeHtml(meta.label)}</span></div>
        <span class="material-symbols-outlined text-secondary group-hover:text-primary transition-colors shrink-0" style="font-size: 14px;">open_in_new</span>
      </a>`;
    }).join('') || `<div class="text-secondary font-body-sm text-body-sm">${escapeHtml(translatePhrase('Pending Setup'))}</div>`;
    const reviews = deterministicMetric(store.jde, 24, 420);
    const rating = (4 + deterministicMetric(store.store_name, 0, 9) / 10).toFixed(1);
    aside.innerHTML = `
      <div class="bg-surface-container-lowest border border-outline-variant p-5 flex flex-col gap-2 relative shadow-[4px_4px_0px_0px_rgba(226,226,226,0.5)]">
        <button class="absolute top-4 right-4 text-secondary hover:text-primary transition-colors" type="button" data-action="store-detail-close"><span class="material-symbols-outlined">close</span></button>
        <div class="flex items-center gap-2 flex-wrap"><span class="font-label-caps text-label-caps text-secondary bg-surface-container px-2 py-0.5 border border-outline-variant whitespace-nowrap">JDE ${escapeHtml(store.jde || '-')}</span><span class="bg-primary text-on-primary font-label-caps text-[9px] px-2 py-0.5 uppercase tracking-wider whitespace-nowrap">${escapeHtml(translatePhrase(platforms.length ? 'Active' : 'Pending'))}</span></div>
        <h2 class="font-headline-md text-headline-md text-primary mt-1 break-words">${escapeHtml(store.store_name || '-')}</h2>
        <div class="flex items-start gap-1 text-secondary font-body-sm text-body-sm"><span class="material-symbols-outlined shrink-0" style="font-size: 16px;">location_on</span><span class="break-words">${escapeHtml(storeLocation(store))}</span></div>
      </div>
      <div class="flex flex-col xl:flex-row gap-4">
        <div class="flex-1 bg-surface-container-lowest border border-outline-variant p-4 flex flex-col gap-3 min-w-[160px]">
          <h3 class="font-label-caps text-label-caps text-secondary border-b border-outline-variant pb-2 break-words">${escapeHtml(translatePhrase('Data Capabilities'))}</h3>
          <ul class="space-y-2 font-body-sm text-body-sm">
            ${capabilityLine('Reviews', platforms.length > 0)}
            ${capabilityLine('Photos', hasPhotos)}
            ${capabilityLine('Translation', hasTranslation)}
            ${capabilityLine('Order Details', hasOrder)}
          </ul>
        </div>
        <div class="flex-1 bg-surface-container-lowest border border-outline-variant p-4 flex flex-col gap-3 min-w-[160px]">
          <h3 class="font-label-caps text-label-caps text-secondary border-b border-outline-variant pb-2 break-words">${escapeHtml(translatePhrase('Platform Entry'))}</h3>
          <div class="space-y-2">${entries}</div>
        </div>
      </div>
      <div class="bg-surface-container-lowest border border-outline-variant p-4 flex flex-col gap-4">
        <div class="flex items-center justify-between border-b border-outline-variant pb-2 gap-2 flex-wrap"><h3 class="font-label-caps text-label-caps text-secondary break-words">${selectedDays()}-${lang() === 'zh' ? '\u5929\u8bc4\u8bba\u6458\u8981' : 'DAY REVIEW SUMMARY'}</h3><span class="font-label-caps text-label-caps text-primary bg-surface-container px-2 border border-outline-variant whitespace-nowrap shrink-0">${escapeHtml(translatePhrase('AUTO-SYNC ON'))}</span></div>
        <div class="flex flex-wrap gap-4 justify-between"><div class="flex flex-col gap-1 min-w-[120px]"><span class="font-body-sm text-body-sm text-secondary truncate">${escapeHtml(translatePhrase('Total Ingestion'))}</span><span class="font-display-lg text-display-lg text-primary font-bold">${reviews}</span></div><div class="flex flex-col gap-1 min-w-[120px]"><span class="font-body-sm text-body-sm text-secondary truncate">${escapeHtml(translatePhrase('Avg Rating'))}</span><div class="flex items-end gap-1"><span class="font-display-lg text-display-lg text-primary font-bold">${rating}</span><span class="font-body-sm text-body-sm text-secondary mb-1 whitespace-nowrap">/ 5.0</span></div></div></div>
      </div>`;
    aside.querySelectorAll('[data-no-url="true"]').forEach(link => link.addEventListener('click', event => {
      event.preventDefault();
      const key = link.dataset.platformEntry;
      const capability = capabilities[key] || {};
      showModal('Platform Execution Path', `${platformLabel(key)}\nExecutor: ${capability.executor || 'not registered'}\nOrder details: ${capability.supports_order_detail ? 'supported' : 'not supported'}\nRead-only detail: ${capability.read_only_detail !== false ? 'yes' : 'no'}\n\nNo direct store URL is present in the registry, so this platform uses portal navigation plus store selection.`);
    }));
  }
  function renderStoreCoverage() {
    const state = window.__heyteaStoreCoverage;
    if (!state) return;
    const rows = filteredStoreCoverageRows();
    const pageSize = state.pageSize || 10;
    const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
    state.page = Math.min(Math.max(1, state.page || 1), totalPages);
    const pageRows = rows.slice((state.page - 1) * pageSize, state.page * pageSize);
    const tbody = document.querySelector('main table tbody');
    if (tbody) {
      tbody.innerHTML = pageRows.map((store, index) => {
        const platforms = storePlatformKeys(store);
        const selected = state.selectedJde === store.jde || (!state.selectedJde && index === 0);
        const reviews = deterministicMetric(store.jde, 24, 420).toLocaleString();
        return `<tr class="border-b border-outline-variant ${selected ? 'bg-surface-container-low ' : ''}cursor-pointer hover:bg-surface-container transition-colors" data-jde="${escapeHtml(store.jde)}">
          <td class="py-2 px-3 font-data-mono text-data-mono text-primary">${escapeHtml(store.jde || '-')}</td>
          <td class="py-2 px-3 font-semibold text-primary">${escapeHtml(store.store_name || '-')}</td>
          <td class="py-2 px-3 text-secondary">${escapeHtml(storeLocation(store))}</td>
          <td class="py-2 px-3"><div class="flex justify-center gap-1">${platforms.slice(0, 5).map(key => platformIconHtml(key, true)).join('') || platformIconHtml('pending', false)}</div></td>
          <td class="py-2 px-3 text-right font-data-mono text-data-mono text-secondary">${platforms.length ? `${deterministicMetric(store.jde, 1, 23)}h ago` : '-'}</td>
          <td class="py-2 px-3 text-right font-data-mono text-data-mono text-primary">${platforms.length ? reviews : '0'}</td>
          <td class="py-2 px-3"><span class="${platforms.length ? 'bg-primary text-on-primary' : 'bg-surface-container-high text-on-surface border border-outline-variant'} font-label-caps text-[9px] px-2 py-0.5 uppercase tracking-wider">${escapeHtml(translatePhrase(platforms.length ? 'Covered' : 'Pending Setup'))}</span></td>
        </tr>`;
      }).join('');
      tbody.querySelectorAll('tr[data-jde]').forEach(row => row.addEventListener('click', () => {
        state.selectedJde = row.dataset.jde;
        renderStoreCoverage();
      }));
    }
    const selected = rows.find(store => store.jde === state.selectedJde) || rows[0] || state.stores[0];
    if (selected) {
      state.selectedJde = selected.jde;
      renderStoreDetail(selected);
    }
    const footer = Array.from(document.querySelectorAll('main section > div')).find(node => cleanText(node).includes('Showing') || cleanText(node).includes('\u663e\u793a'));
    if (footer) {
      const start = rows.length ? (state.page - 1) * pageSize + 1 : 0;
      const end = Math.min(rows.length, state.page * pageSize);
      footer.innerHTML = `<span>${escapeHtml(translatePhrase('Showing'))} ${start} to ${end} of ${rows.length} ${escapeHtml(translatePhrase('Stores'))}</span><div class="flex items-center gap-2"><button type="button" data-store-page="prev" class="w-8 h-8 flex items-center justify-center border border-outline-variant hover:border-primary transition-colors ${state.page <= 1 ? 'opacity-50' : ''}"><span class="material-symbols-outlined" style="font-size: 18px;">chevron_left</span></button><span class="font-data-mono text-primary">${state.page} / ${totalPages}</span><button type="button" data-store-page="next" class="w-8 h-8 flex items-center justify-center border border-outline-variant hover:border-primary transition-colors text-primary ${state.page >= totalPages ? 'opacity-50' : ''}"><span class="material-symbols-outlined" style="font-size: 18px;">chevron_right</span></button></div>`;
      footer.querySelector('[data-store-page="prev"]').addEventListener('click', event => { event.preventDefault(); event.stopPropagation(); if (state.page > 1) { state.page -= 1; renderStoreCoverage(); } });
      footer.querySelector('[data-store-page="next"]').addEventListener('click', event => { event.preventDefault(); event.stopPropagation(); if (state.page < totalPages) { state.page += 1; renderStoreCoverage(); } });
    }
  }
  async function initStoreCoveragePage() {
    if (pageByPath() !== 'store_coverage') return;
    try {
      const [status, registry] = await Promise.all([getUnifiedStatus(), apiJson('/api/unified/stores?limit=1000')]);
      const stores = registry.stores || [];
      window.__heyteaStoreCoverage = { status, stores, page: 1, pageSize: 10, selectedJde: stores[0]?.jde || '', country: '', platform: '', jde: '', query: '' };
      const selects = Array.from(document.querySelectorAll('main select'));
      const countries = Array.from(new Set(stores.map(store => normalizeRegionText(String(store.country || '').trim())).filter(Boolean))).sort();
      const platformKeys = Array.from(new Set(stores.flatMap(store => storePlatformKeys(store)))).sort();
      if (selects[0]) {
        selects[0].innerHTML = `<option value="">${escapeHtml(translatePhrase('All Regions'))}</option>${countries.map(country => `<option value="${escapeHtml(country)}">${escapeHtml(country)}</option>`).join('')}`;
        selects[0].addEventListener('change', () => { window.__heyteaStoreCoverage.country = selects[0].value; window.__heyteaStoreCoverage.page = 1; renderStoreCoverage(); });
      }
      if (selects[1]) {
        selects[1].innerHTML = `<option value="">${escapeHtml(translatePhrase('All Platforms'))}</option>${platformKeys.map(key => `<option value="${escapeHtml(key)}">${escapeHtml(platformLabel(key))}</option>`).join('')}`;
        selects[1].addEventListener('change', () => { window.__heyteaStoreCoverage.platform = canonicalUiPlatform(selects[1].value); window.__heyteaStoreCoverage.page = 1; renderStoreCoverage(); });
      }
      const inputs = Array.from(document.querySelectorAll('main input'));
      if (inputs[0]) inputs[0].addEventListener('input', () => { window.__heyteaStoreCoverage.jde = inputs[0].value; window.__heyteaStoreCoverage.page = 1; renderStoreCoverage(); });
      if (inputs[1]) inputs[1].addEventListener('input', () => { window.__heyteaStoreCoverage.query = inputs[1].value; window.__heyteaStoreCoverage.page = 1; renderStoreCoverage(); });
      renderStoreCoverage();
    } catch (error) {
      notify(`Store coverage load failed: ${error.message || error}`);
    }
  }
  function reviewCountry(review) {
    return normalizeRegionText(String(review.country || '').trim()) || '-';
  }
  function reviewPlatform(review) {
    return String(review.platform || '').trim() || '-';
  }
  function reviewStore(review) {
    return String(review.store || '').trim() || '-';
  }
  function reviewRating(review) {
    const match = String(review.rating || '').match(/-?\d+(\.\d+)?/);
    const value = Number(match ? match[0] : 0);
    return Number.isFinite(value) && value > 0 ? value : '';
  }
  function reviewSentiment(review) {
    const rating = reviewRating(review);
    if (rating && rating <= 2) return 'Negative';
    if (rating && rating >= 4) return 'Positive';
    return 'Neutral';
  }
  function reviewQuality(review) {
    const flags = Array.isArray(review.quality_flags) ? review.quality_flags.filter(Boolean) : [];
    if (flags.length) return flags[0];
    if (review.has_order) return 'ORDER';
    if (review.has_image) return 'IMAGE';
    return '-';
  }
  function reviewShort(text, max = 120) {
    const value = String(text || '').replace(/\s+/g, ' ').trim();
    return value.length > max ? value.slice(0, max - 1) + '…' : value;
  }
  function validReviewText(value) {
    const text = String(value ?? '').replace(/\s+/g, ' ').trim();
    if (!text || ['-', 'none', 'null', 'no data', 'n/a', 'empty'].includes(text.toLowerCase())) return '';
    if (/^[\d\s:：\-.,，。/]+$/.test(text)) return '';
    return text;
  }
  function isNoiseOrderDetail(value) {
    const text = String(value ?? '').trim();
    if (!validReviewText(text)) return true;
    const cleaned = cleanOrderDetailText(text);
    if (!validReviewText(cleaned)) return true;
    const lower = text.toLowerCase();
    const markers = ['order', 'item', 'qty', 'quantity', 'price', 'subtotal', 'total', 'product', 'goods', '订单', '商品', '数量', '单价', '价格', '小计', '结算'];
    const hasMarker = markers.some(marker => lower.includes(marker.toLowerCase()));
    const hasMoney = /(?:[$€£¥]|HK\$|MOP|RM|SGD|USD|AUD|CAD)\s*\d/i.test(text);
    const hasQuantity = /(?:^|\s)(?:x\s*)?\d+\s*(?:份|杯|件|pcs?|items?)\b/i.test(text);
    return !(hasMarker || hasMoney || hasQuantity);
  }
  function cleanOrderDetailText(value) {
    return String(value ?? '')
      .replace(/\r/g, '\n')
      .split('\n')
      .map(line => line.trim())
      .filter(line => {
        if (!line) return false;
        const lower = line.toLowerCase();
        if (/^[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}$/.test(line)) return false;
        if (lower.includes('.owner') || lower.includes('owner a') || lower.includes('owner b')) return false;
        if (/^[A-Za-z]:[\\/].+/.test(line) || /exports[\\/].+\.jsonl?$/i.test(line)) return false;
        return true;
      })
      .join('\n')
      .trim();
  }
  function cleanCustomerDisplay(value) {
    return String(value ?? '')
      .replace(/\b[a-fA-F0-9]{16,64}\b/g, '')
      .replace(/\s+/g, ' ')
      .trim();
  }
  function cleanReviewIdentityValue(value, max = 220) {
    const text = String(value ?? '').replace(/\s+/g, ' ').trim();
    if (!text || ['-', 'none', 'null', 'no data', 'n/a'].includes(text.toLowerCase())) return '';
    return text.toLowerCase().slice(0, max);
  }
  function reviewFuzzyBaseKey(review) {
    const platform = canonicalUiPlatform(review.platform || '');
    const store = cleanReviewIdentityValue(review.store || review.store_id, 160);
    const rating = cleanReviewIdentityValue(review.rating, 20);
    const reviewTime = cleanReviewIdentityValue(String(review.review_time || '').slice(0, 16), 40);
    return `${platform}|${store}|${rating}|${reviewTime}`;
  }
  function reviewTextIdentity(review, max = 2000) {
    const text = String(review?.review || review?.translated_review || '')
      .replace(/[\ue000-\uf8ff]/g, ' ')
      .replace(/(?:…|\.\.\.)\s*(?:更多|more|show\s+more).*$/is, '');
    return cleanReviewIdentityValue(text, max);
  }
  function sameReviewText(left, right) {
    if (!left || !right) return false;
    if (left === right) return true;
    const shorter = left.length <= right.length ? left : right;
    const longer = left.length <= right.length ? right : left;
    if (shorter.length < 40) return false;
    if (longer.includes(shorter)) return true;
    if (shorter.length >= 80 && shorter.slice(0, 96) === longer.slice(0, 96)) return true;
    const a = shorter.slice(0, 800);
    const b = longer.slice(0, 800);
    const grams = value => {
      const out = new Set();
      for (let i = 0; i < Math.max(1, value.length - 2); i += 1) out.add(value.slice(i, i + 3));
      return out;
    };
    const ga = grams(a);
    const gb = grams(b);
    let hits = 0;
    ga.forEach(item => { if (gb.has(item)) hits += 1; });
    return hits / Math.max(1, Math.min(ga.size, gb.size)) >= 0.88;
  }
  function reviewIdentityKey(review) {
    const platform = canonicalUiPlatform(review.platform || '');
    const orderId = cleanReviewIdentityValue(review.order_id || review.order_sn || extractOrderIdFromText(review.order_detail || ''), 120);
    if (orderId) return `order|${platform}|${orderId}`;
    const store = cleanReviewIdentityValue(review.store || review.store_id, 160);
    const customer = cleanReviewIdentityValue(review.customer, 120);
    const rating = cleanReviewIdentityValue(review.rating, 20);
    if (platform === 'google_maps' && store && customer) return `google_user|${platform}|${store}|${customer}|${rating}`;
    const reviewText = cleanReviewIdentityValue(review.review || review.translated_review, 260);
    if (reviewText) return `text|${platform}|${store}|${customer}|${rating}|${reviewText}`;
    const reviewId = cleanReviewIdentityValue(review.review_id, 160);
    const sourceFile = cleanReviewIdentityValue(review.source_file, 240);
    const reviewIdBase = reviewId.replace(/[-_]\d{1,6}$/, '');
    if (reviewId && reviewId.length >= 10 && sourceFile && !sourceFile.includes(reviewId) && !sourceFile.includes(reviewIdBase)) return `review_id|${platform}|${reviewId}`;
    const reviewTime = cleanReviewIdentityValue(String(review.review_time || '').slice(0, 10), 40);
    if (reviewTime || customer || store || rating) return `rating_only|${platform}|${reviewTime}|${customer}|${rating}|${store}`;
    return `fallback|${platform}|${sourceFile}`;
  }
  function meaningfulReviewValue(value) {
    if (value === undefined || value === null) return false;
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === 'object') return Object.keys(value).length > 0;
    const text = String(value).trim();
    return Boolean(text) && !['-', 'none', 'null', 'no data', 'n/a'].includes(text.toLowerCase());
  }
  function reviewCompletenessScore(review) {
    let score = 0;
    ['platform', 'country', 'store', 'store_id', 'rating', 'review', 'translated_review', 'customer', 'review_time', 'order_id'].forEach(field => {
      if (meaningfulReviewValue(review[field])) score += 4;
    });
    if (Array.isArray(review.ordered_items) && review.ordered_items.length) {
      score += 18 + Math.min(review.ordered_items.length, 8);
      score += review.ordered_items.filter(item => item && meaningfulReviewValue(orderedItemPrice(item))).length;
    }
    if (meaningfulReviewValue(review.order_detail)) score += 18 + Math.min(String(review.order_detail || '').length, 300) / 30;
    if (Array.isArray(review.image_urls) && review.image_urls.length) score += 10 + Math.min(review.image_urls.length, 6);
    if (/exports[\\/]+runs/i.test(String(review.source_file || ''))) score += 6;
    return score;
  }
  function mergeReviewRecords(existing, incoming) {
    const primary = reviewCompletenessScore(incoming) > reviewCompletenessScore(existing) ? incoming : existing;
    const secondary = primary === incoming ? existing : incoming;
    const merged = { ...primary };
    Object.entries(secondary || {}).forEach(([key, value]) => {
      if (!meaningfulReviewValue(merged[key]) && meaningfulReviewValue(value)) {
        merged[key] = value;
        return;
      }
      if (key === 'image_urls') {
        const urls = [];
        [merged[key], value].forEach(list => (Array.isArray(list) ? list : [list]).forEach(url => {
          if (meaningfulReviewValue(url) && !urls.includes(url)) urls.push(url);
        }));
        merged[key] = urls;
      } else if (key === 'ordered_items') {
        const current = Array.isArray(merged[key]) ? merged[key] : [];
        const extra = Array.isArray(value) ? value : [];
        if (orderItemsScore(extra) > orderItemsScore(current) || (orderItemsScore(extra) === orderItemsScore(current) && normalizeOrderItemsForDisplay(extra).length > normalizeOrderItemsForDisplay(current).length)) {
          merged[key] = extra;
        }
      } else if (key === 'order_detail' && String(value || '').length > String(merged[key] || '').length) {
        merged[key] = value;
      } else if (key === 'raw_json' && merged[key] && value && typeof merged[key] === 'object' && typeof value === 'object') {
        merged[key] = { ...value, ...merged[key] };
      }
    });
    merged.has_order = Boolean(merged.order_id || meaningfulReviewValue(merged.order_detail) || (Array.isArray(merged.ordered_items) && merged.ordered_items.length));
    merged.has_image = Boolean(Array.isArray(merged.image_urls) && merged.image_urls.length);
    return merged;
  }
  function dedupeReviewRecords(reviews) {
    const byKey = new Map();
    const fuzzyBuckets = new Map();
    (Array.isArray(reviews) ? reviews : []).forEach(review => {
      review.order_detail = cleanOrderDetailText(review?.order_detail);
      if (isNoiseOrderDetail(review?.order_detail)) review.order_detail = '';
      review.review = validReviewText(review?.review);
      review.translated_review = validReviewText(review?.translated_review);
      review.customer = cleanCustomerDisplay(review?.customer);
      const reviewText = cleanReviewIdentityValue(review?.review || review?.translated_review, 80);
      const placeholderOnly = ['no data', '暂无', '暂无数据', 'empty', 'n/a'].includes(reviewText)
        && !meaningfulReviewValue(review?.order_id)
        && !meaningfulReviewValue(review?.order_detail)
        && !(Array.isArray(review?.ordered_items) && review.ordered_items.length)
        && !(Array.isArray(review?.image_urls) && review.image_urls.length);
      if (placeholderOnly) return;
      const rawReviewText = String(review?.review || review?.translated_review || '').trim();
      const platformKey = canonicalUiPlatform(review?.platform || '');
      const hasCoreReviewEvidence = meaningfulReviewValue(review?.rating)
        || meaningfulReviewValue(review?.review_time)
        || meaningfulReviewValue(review?.order_id);
      if (platformKey === 'dianping' && !(meaningfulReviewValue(review?.rating) || meaningfulReviewValue(review?.review_time))) return;
      if (!hasCoreReviewEvidence && /(商户服务|关于我们|请登录|登录\/注册|去\s*APP\s*查看更多内容|查看更多内容|美食|中国最贵的将军墓|上千瓶茅台|网红大滑梯|这个商场惊见|privacy policy|terms of use|sign in|log in|register|download app)/i.test(rawReviewText)) return;
      const rawKey = reviewIdentityKey(review || {});
      let key = rawKey;
      const text = reviewTextIdentity(review || {});
      if (!byKey.has(rawKey) && rawKey.startsWith('text|') && text) {
        const bucketKey = reviewFuzzyBaseKey(review || {});
        const bucket = fuzzyBuckets.get(bucketKey) || [];
        const matched = bucket.find(candidateKey => sameReviewText(text, reviewTextIdentity(byKey.get(candidateKey))));
        if (matched) key = matched;
      }
      byKey.set(key, byKey.has(key) ? mergeReviewRecords(byKey.get(key), review) : review);
      if (key.startsWith('text|') && text) {
        const bucketKey = reviewFuzzyBaseKey(review || {});
        const bucket = fuzzyBuckets.get(bucketKey) || [];
        if (!bucket.includes(key)) bucket.push(key);
        fuzzyBuckets.set(bucketKey, bucket);
      }
    });
    return Array.from(byKey.values());
  }
  function starsHtml(rating) {
    const score = Math.max(0, Math.min(5, Math.round(Number(rating || 0))));
    return `<span class="font-data-mono text-data-mono">${'★'.repeat(score)}${'☆'.repeat(5 - score)}</span>`;
  }
  function extractOrderIdFromText(value) {
    const text = String(value || '');
    const explicit = text.match(/(?:订单号|訂單號|order\s*(?:id|no\.?|number|#))\s*[:：#]?\s*([A-Z]{0,6}\d{6,})/i);
    if (explicit) return explicit[1];
    const loose = text.match(/\b([A-Z]{1,6}\d{7,})\b/);
    return loose ? loose[1] : '';
  }
  function isMostlyChineseText(text) {
    const value = String(text || '').trim();
    if (!value) return false;
    const matches = value.match(/[\u4e00-\u9fff]/g) || [];
    return (matches.length / Math.max(1, value.length)) >= 0.3;
  }
  function looksTraditionalChinese(text) {
    const value = String(text || '');
    return /[體臺萬與為說評價後廣門點開關顧飲龍東線區應轉譯圖單訂對於沒麼讓將會個員請處層發現滿意推薦變溫遞遲遜舊嚴靜雲灣價錢裡還聯繫衛質選擇傳實驗證標準]/.test(value);
  }
  function reviewTranslationText(review) {
    const translated = String(review.translated_review || '').trim();
    if (translated && translated !== '-') {
      if (isMostlyChineseText(translated) && looksTraditionalChinese(translated)) return '';
      return translated;
    }
    const cached = String(review.cn_translation || '').trim();
    if (cached && cached !== '-') return cached;
    return '';
  }
  function orderedItemName(item) {
    return item.product_name || item.productName || item.spuName || item.name || item.item || item.itemName || item.product || item.text || '-';
  }
  function orderedItemSpecs(item) {
    return item.sku_name || item.skuName || item.specs || item.spec || item.options || item.groupProductNames || item.desc || item.remark || '';
  }
  function orderedItemQty(item) {
    const direct = item.quantity || item.qty || item.count || item.productCount || item.num || '';
    if (String(direct || '').trim()) return direct;
    const text = `${item.text || ''} ${item.name || ''} ${item.item || ''}`;
    const match = text.match(/[xX×]\s*(\d+)/) || text.match(/数量[:：]?\s*(\d+)/i) || text.match(/qty[:：]?\s*(\d+)/i);
    return match ? match[1] : '';
  }
  function orderedItemPrice(item) {
    const value = item.unit_price || item.unitPrice || item.price || item.amount || item.productPrice || item.totalPrice || item.order_total
      || item.priceStr || item.goodsPrice || item.salePrice || item.finalPrice || item.singlePrice || item.subtotal || '';
    const textValue = String(value || '').trim();
    if (textValue) return textValue;
    const merged = `${item.text || ''} ${item.spec || ''} ${item.specs || ''} ${item.desc || ''} ${item.detail || ''} ${item.remark || ''}`;
    const matches = merged.match(/(?:HK\$|US\$|C\$|A\$|SG\$|[$¥￥€£₩]|RM)?\s*-?\d{1,6}(?:[.,]\d{1,2})?/g) || [];
    const pick = matches.map(x => String(x || '').trim()).filter(x => /\d/.test(x)).pop() || '';
    return pick;
  }
  function orderItemScore(item) {
    if (!item || typeof item !== 'object') return 0;
    const serialized = JSON.stringify(item);
    const name = orderedItemName(item);
    const qty = orderedItemQty(item);
    const price = orderedItemPrice(item);
    let score = 0;
    if (name && name !== '-') score += 2;
    if (qty) score += 3;
    if (price) score += 5;
    if (/(商品|產品|产品|饮品|飲品|goods|product|item|price|单价|單價)/i.test(serialized)) score += 2;
    if (/^(纽约|紐約|曼哈顿|曼哈頓|洛杉矶|洛杉磯|旧金山|舊金山|西雅图|西雅圖|United States|Canada|Australia|Singapore|Malaysia)$/i.test(String(name || '').trim())) score -= 10;
    return score;
  }
  function normalizeOrderItemsForDisplay(items) {
    return (Array.isArray(items) ? items : [])
      .filter(item => orderItemScore(item) > 1)
      .filter((item, index, all) => {
        const key = `${orderedItemName(item)}|${orderedItemSpecs(item)}|${orderedItemQty(item)}|${orderedItemPrice(item)}`;
        return all.findIndex(peer => `${orderedItemName(peer)}|${orderedItemSpecs(peer)}|${orderedItemQty(peer)}|${orderedItemPrice(peer)}` === key) === index;
      });
  }
  function orderItemsScore(items) {
    return normalizeOrderItemsForDisplay(items).reduce((sum, item) => sum + orderItemScore(item), 0);
  }
  function extractOrderFallback(raw) {
    const containers = [];
    const texts = [];
    const seen = new Set();
    function walk(node, depth = 0) {
      if (depth > 6 || !node || typeof node !== 'object') return;
      if (seen.has(node)) return;
      seen.add(node);
      if (Array.isArray(node)) {
        node.forEach(item => walk(item, depth + 1));
        return;
      }
      Object.entries(node).forEach(([key, value]) => {
        const keyNorm = String(key || '').toLowerCase().replace(/[\s_-]/g, '');
        if (/(orderdetail|orderdetails|items|products|goods|detail|orderitem)/.test(keyNorm)) containers.push(value);
        if (typeof value === 'string') {
          const text = value.trim();
          if (text && /(name|spec|qty|price|remark|detail|item|product)/.test(keyNorm)) texts.push(text);
        } else if (value && typeof value === 'object') {
          walk(value, depth + 1);
        }
      });
    }
    walk(raw || {});
    const items = [];
    const pushItem = candidate => {
      if (!candidate) return;
      if (Array.isArray(candidate)) {
        candidate.forEach(item => pushItem(item));
        return;
      }
      if (typeof candidate === 'object') {
        const name = orderedItemName(candidate);
        if (name && name !== '-' && orderItemScore(candidate) > 1) items.push(candidate);
        Object.values(candidate).forEach(value => {
          if (value && typeof value === 'object') pushItem(value);
        });
      }
    };
    containers.forEach(item => pushItem(item));
    return {
      items: normalizeOrderItemsForDisplay(items),
      detail: texts.join('\n').slice(0, 12000),
    };
  }
  async function ensureReviewTranslation(review, aside, force = false) {
    const node = aside.querySelector('[data-review-translation]');
    if (!node) return;
    const translated = reviewTranslationText(review);
    if (translated && !force) {
      node.textContent = translated;
      review.translated_review = translated;
      if (isMostlyChineseText(translated) && looksTraditionalChinese(translated)) {
        try {
          const normalized = await apiJson('/api/unified/translate', {
            method: 'POST',
            body: JSON.stringify({ text: translated, review_id: review.review_id || '', force_simplified: true }),
          });
          if (normalized?.translated) {
            review.translated_review = String(normalized.translated);
            review.cn_translation = review.translated_review;
            node.textContent = review.translated_review;
          }
        } catch (_ignore) {}
      }
      return;
    }
    const source = validReviewText(review.review);
    if (!source || source === '-') {
      node.textContent = lang() === 'zh' ? '暂无译文' : 'No translation captured';
      return;
    }
    const cacheKey = String(review.review_id || source.slice(0, 256));
    window.__heyteaTranslationCache = window.__heyteaTranslationCache || {};
    if (force) {
      delete window.__heyteaTranslationCache[cacheKey];
      review.translated_review = '';
      review.cn_translation = '';
    }
    if (!force && window.__heyteaTranslationCache[cacheKey]) {
      review.translated_review = window.__heyteaTranslationCache[cacheKey];
      node.textContent = review.translated_review;
      return;
    }
    node.textContent = lang() === 'zh' ? '翻译中...' : 'Translating...';
    try {
      const result = await apiJson('/api/unified/translate', {
        method: 'POST',
        body: JSON.stringify({ text: source, review_id: review.review_id || '', force_simplified: true, force }),
      });
      if (result && result.translated) {
        review.translated_review = String(result.translated);
        review.cn_translation = review.translated_review;
        window.__heyteaTranslationCache[cacheKey] = review.translated_review;
        node.textContent = review.translated_review;
        renderReviewWorkbench();
      } else {
        review.translated_review = source;
        node.textContent = review.translated_review;
      }
    } catch (_error) {
      review.translated_review = source;
      node.textContent = review.translated_review;
    }
  }
  function renderReviewDetail(review) {
    const aside = document.querySelector('main > div:last-child');
    if (!aside) return;
    if (!review) {
      aside.innerHTML = `<div class="p-container-padding"><h3 class="font-headline-md text-headline-md text-primary">${escapeHtml(translatePhrase('No real review records found'))}</h3><p class="mt-3 text-secondary">${escapeHtml(translatePhrase('Run a collector or widen the date range to 30 days.'))}</p></div>`;
      return;
    }
    const rating = reviewRating(review);
    const images = Array.isArray(review.image_urls) ? review.image_urls : [];
    const fallbackOrder = extractOrderFallback(review.raw_json || {});
    const directItems = normalizeOrderItemsForDisplay(review.ordered_items);
    const items = directItems.length ? directItems : fallbackOrder.items;
    const originalText = validReviewText(review.review);
    const noTextLabel = lang() === 'zh' ? '该评价无文字内容，仅保留评分、图片或订单详情。' : 'No written review was captured; rating, images or order details are retained.';
    const cleanedOrderDetail = cleanOrderDetailText(review.order_detail);
    const orderDetailCandidate = isNoiseOrderDetail(cleanedOrderDetail) ? '' : cleanedOrderDetail;
    const orderDetailText = orderDetailCandidate || fallbackOrder.detail || '-';
    const orderTotal = String(review.order_total || '').trim();
    aside.innerHTML = `<div class="p-container-padding border-b border-outline-variant bg-[#F5F5F5] sticky top-0 z-20">
      <div class="flex justify-between items-start mb-2 gap-2"><h3 class="font-headline-md text-headline-md text-primary">${escapeHtml(translatePhrase('Review Details'))}</h3><div class="flex gap-2 flex-wrap"><span class="inline-block px-2 py-0.5 bg-surface-container-highest border border-outline-variant text-primary font-label-caps text-label-caps uppercase rounded-none">${escapeHtml(translatePhrase('Full Text Expanded'))}</span>${review.translated_review ? `<span class="inline-block px-2 py-0.5 bg-primary text-on-primary font-label-caps text-label-caps uppercase rounded-none">${escapeHtml(translatePhrase('Translation Fetched'))}</span>` : ''}</div></div>
      <div class="flex items-center gap-4 text-body-sm text-secondary flex-wrap"><span class="flex items-center gap-1 font-data-mono text-data-mono"><span class="material-symbols-outlined text-[14px]">calendar_today</span>${escapeHtml(review.review_time || '-')}</span><span class="flex items-center gap-1 font-medium text-primary"><span class="material-symbols-outlined text-[14px]">store</span>${escapeHtml(reviewStore(review))}</span><span class="flex items-center gap-1 text-error"><span class="material-symbols-outlined text-[14px]" style="font-variation-settings: 'FILL' 1;">star</span>${escapeHtml(rating || '-')}</span></div>
    </div>
    <div class="p-container-padding space-y-6 flex-1">
      <div><h4 class="font-label-caps text-label-caps text-secondary uppercase mb-2 border-b border-outline-variant pb-1">${escapeHtml(translatePhrase('Content Analysis'))}</h4><div class="grid grid-cols-2 gap-4">
        <div class="p-3 bg-background border border-outline-variant rounded-none"><span class="block font-label-caps text-label-caps text-secondary uppercase mb-2">${escapeHtml(translatePhrase('Original Text'))}</span><p class="font-body-md text-primary leading-relaxed whitespace-pre-wrap">${escapeHtml(originalText || noTextLabel)}</p></div>
        <div class="p-3 bg-surface-container-low border border-outline-variant rounded-none"><span class="block font-label-caps text-label-caps text-secondary uppercase mb-2">${escapeHtml(translatePhrase('Chinese Translation'))}</span><p data-review-translation class="font-body-md text-secondary leading-relaxed whitespace-pre-wrap">${escapeHtml(reviewTranslationText(review) || (lang() === 'zh' ? '翻译中…' : 'Translating…'))}</p></div>
      </div></div>
      <div><h4 class="font-label-caps text-label-caps text-secondary uppercase mb-2 border-b border-outline-variant pb-1">${escapeHtml(translatePhrase('Evidence Images'))}</h4><div class="flex gap-2 overflow-x-auto pb-2">${images.length ? images.map(url => `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer" class="w-24 h-24 shrink-0 border border-outline-variant bg-surface-container-low hover:border-primary transition-colors"><img alt="review evidence" class="w-full h-full object-cover" src="${escapeHtml(url)}"></a>`).join('') : `<span class="text-secondary">-</span>`}</div></div>
      <div><div class="flex justify-between items-center mb-2 border-b border-outline-variant pb-1"><h4 class="font-label-caps text-label-caps text-secondary uppercase">${escapeHtml(translatePhrase('Associated Order'))}</h4><span class="font-data-mono text-data-mono text-secondary text-[11px]">ID: ${escapeHtml(review.order_id || '-')}</span></div>
        ${items.length ? `<div class="border border-outline-variant bg-surface-container-lowest"><table class="w-full text-left"><thead class="bg-surface-container-low font-label-caps text-label-caps text-secondary uppercase"><tr><th class="p-2 font-normal">${escapeHtml(translatePhrase('Item'))}</th><th class="p-2 font-normal">${escapeHtml(translatePhrase('Specs'))}</th><th class="p-2 font-normal text-right w-12">${escapeHtml(translatePhrase('Qty'))}</th><th class="p-2 font-normal text-right w-16">${escapeHtml(translatePhrase('Price'))}</th></tr></thead><tbody class="font-body-sm text-primary divide-y divide-outline-variant">${items.map(item => `<tr><td class="p-2">${escapeHtml(orderedItemName(item))}</td><td class="p-2 text-secondary text-[12px]">${escapeHtml(orderedItemSpecs(item))}</td><td class="p-2 text-right font-data-mono text-data-mono">${escapeHtml(orderedItemQty(item))}</td><td class="p-2 text-right font-data-mono text-data-mono">${escapeHtml(orderedItemPrice(item))}</td></tr>`).join('')}</tbody></table></div>` : ''}
        ${orderTotal ? `<div class="mt-2 text-right font-data-mono text-data-mono text-primary">${escapeHtml(translatePhrase('Order Total'))}: ${escapeHtml(orderTotal)}</div>` : ''}
        ${orderDetailText && orderDetailText !== '-' ? `<pre class="mt-2 border border-outline-variant bg-surface-container-lowest p-3 whitespace-pre-wrap text-body-sm">${escapeHtml(orderDetailText)}</pre>` : (!items.length ? `<pre class="border border-outline-variant bg-surface-container-lowest p-3 whitespace-pre-wrap text-body-sm">-</pre>` : '')}
      </div>
      <div><h4 class="font-label-caps text-label-caps text-secondary uppercase mb-2 border-b border-outline-variant pb-1 flex justify-between">${escapeHtml(translatePhrase('Raw API Payload'))}<span class="font-data-mono text-data-mono text-secondary">${escapeHtml(review.source_file || '')}</span></h4><div class="bg-primary-container text-[#A3DEFE] p-3 font-data-mono text-data-mono text-[11px] overflow-x-auto border border-primary rounded-none"><pre class="m-0"><code>${escapeHtml(JSON.stringify(review.raw_json || review, null, 2))}</code></pre></div></div>
    </div><div class="p-container-padding border-t border-outline-variant bg-[#F5F5F5] mt-auto grid grid-cols-2 gap-2"><button type="button" data-force-retranslate="true" class="bg-primary text-on-primary border border-primary py-2 px-3 rounded-none font-label-caps text-label-caps uppercase hover:opacity-90 transition-colors flex justify-center items-center gap-2"><span class="material-symbols-outlined text-[16px]">translate</span>${escapeHtml(lang() === 'zh' ? '强制重翻译' : 'Retranslate')}</button><button type="button" data-export-review="true" class="bg-surface-container-lowest text-primary border border-primary py-2 px-3 rounded-none font-label-caps text-label-caps uppercase hover:bg-surface-container-low transition-colors flex justify-center items-center gap-2"><span class="material-symbols-outlined text-[16px]">download</span>${escapeHtml(translatePhrase('Export Record'))}</button></div>`;
    aside.querySelector('[data-export-review]')?.addEventListener('click', () => download(`review-${review.review_id || 'record'}.json`, JSON.stringify(review, null, 2), 'application/json;charset=utf-8'));
    aside.querySelector('[data-force-retranslate]')?.addEventListener('click', async () => {
      await ensureReviewTranslation(review, aside, true);
      notify(lang() === 'zh' ? '已强制重翻译当前评论' : 'Current review retranslated');
    });
    ensureReviewTranslation(review, aside);
  }
  function filteredWorkbenchReviews() {
    const state = window.__heyteaReviews;
    if (!state) return [];
    return state.reviews.filter(review => {
      if (state.country && reviewCountry(review) !== state.country) return false;
      if (state.platform && reviewPlatform(review) !== state.platform) return false;
      if (state.store && reviewStore(review) !== state.store) return false;
      if (state.hasImage && !review.has_image) return false;
      if (state.hasOrder && !review.has_order) return false;
      if (state.keyword) {
        const haystack = `${review.review || ''} ${review.translated_review || ''}`.toLowerCase();
        if (!haystack.includes(state.keyword.toLowerCase())) return false;
      }
      return true;
    });
  }
  function renderReviewWorkbench() {
    const state = window.__heyteaReviews;
    if (!state) return;
    const rows = filteredWorkbenchReviews();
    const tbody = document.querySelector('main table tbody');
    if (tbody) {
      tbody.innerHTML = rows.length ? rows.map((review, index) => {
        const selected = state.selectedId === review.review_id || (!state.selectedId && index === 0);
        const sentiment = reviewSentiment(review);
        return `<tr class="${selected ? 'bg-surface-container-high ' : ''}border-b border-outline-variant hover:bg-surface-container-low cursor-pointer transition-colors" data-review-id="${escapeHtml(review.review_id)}">
          <td class="py-2 px-3 align-top"><span class="material-symbols-outlined text-[16px] text-primary" style="font-variation-settings: 'FILL' 1;">${canonicalUiPlatform(review.platform).includes('google') ? 'location_on' : 'takeout_dining'}</span></td>
          <td class="py-2 px-3 align-top text-secondary font-data-mono text-data-mono">${escapeHtml(reviewCountry(review))}</td>
          <td class="py-2 px-3 align-top font-medium">${escapeHtml(reviewStore(review))}</td>
          <td class="py-2 px-3 align-top ${Number(review.rating || 0) <= 2 ? 'text-error' : ''}">${starsHtml(review.rating || 0)}</td>
          <td class="py-2 px-3 align-top text-secondary font-data-mono text-data-mono">${escapeHtml(review.review_time || '-')}</td>
          <td class="py-2 px-3 align-top">${escapeHtml(review.customer || '-')}</td>
          <td class="py-2 px-3 align-top min-w-[150px] whitespace-normal">${escapeHtml(reviewShort(validReviewText(review.review) || (lang() === 'zh' ? '无文字评论' : 'No text review')))}</td>
          <td class="py-2 px-3 align-top min-w-[150px] whitespace-normal text-secondary">${escapeHtml(reviewShort(reviewTranslationText(review) || '-'))}</td>
          <td class="py-2 px-3 align-top"><span class="inline-block px-2 py-0.5 ${sentiment === 'Negative' ? 'bg-error text-on-error' : sentiment === 'Positive' ? 'bg-primary text-on-primary' : 'bg-surface-container-highest text-primary'} font-label-caps text-label-caps uppercase rounded-none">${escapeHtml(translatePhrase(sentiment))}</span></td>
          <td class="py-2 px-3 align-top"><span class="inline-block px-2 py-0.5 bg-surface-container-highest text-primary font-label-caps text-label-caps uppercase rounded-none">${escapeHtml(reviewQuality(review))}</span></td>
        </tr>`;
      }).join('') : `<tr><td colspan="10" class="p-6 text-center text-secondary"><strong>${escapeHtml(translatePhrase('No real review records found'))}</strong><br>${escapeHtml(translatePhrase('Run a collector or widen the date range to 30 days.'))}</td></tr>`;
      tbody.querySelectorAll('[data-review-id]').forEach(row => row.addEventListener('click', () => {
        state.selectedId = row.dataset.reviewId;
        renderReviewWorkbench();
      }));
    }
    const selected = rows.find(review => review.review_id === state.selectedId) || rows[0];
    if (selected) state.selectedId = selected.review_id;
    renderReviewDetail(selected);
  }
  async function initReviewWorkbenchPage() {
    if (pageByPath() !== 'review_workbench') return;
    try {
      const [payload, status, registry] = await Promise.all([
        apiJson(`/api/unified/reviews?days=${selectedDays()}&limit=1200`),
        apiJson('/api/unified/status'),
        apiJson('/api/unified/stores?limit=1000'),
      ]);
      const reviews = dedupeReviewRecords(payload.reviews || []);
      const registryStores = Array.isArray(registry.stores) ? registry.stores : [];
      window.__heyteaReviews = { reviews, selectedId: reviews[0]?.review_id || '', country: '', platform: '', store: '', hasImage: false, hasOrder: false, keyword: '' };
      const selects = Array.from(document.querySelectorAll('main select'));
      const countries = Array.from(new Set([
        ...reviews.map(reviewCountry),
        ...registryStores.map(store => normalizeRegionText(String(store.country || '').trim())),
      ].filter(x => x && x !== '-'))).sort();
      const platformsFromReviews = Array.from(new Set(reviews.map(reviewPlatform).filter(x => x && x !== '-')));
      const platformsFromStatus = Object.values(status.platforms || {}).map(item => item?.name).filter(Boolean);
      const platforms = Array.from(new Set([...platformsFromStatus, ...platformsFromReviews])).sort();
      const stores = Array.from(new Set([
        ...reviews.map(reviewStore),
        ...registryStores.map(store => String(store.store_name || '').trim()),
      ].filter(x => x && x !== '-'))).sort();
      if (selects[0]) { selects[0].innerHTML = `<option value="7">${escapeHtml(translatePhrase('Last 7 Days'))}</option><option value="30">${escapeHtml(translatePhrase('Last 30 Days'))}</option>`; selects[0].value = String(selectedDays()); selects[0].addEventListener('change', async () => { setSelectedDays(selects[0].value); await initReviewWorkbenchPage(); }); }
      if (selects[1]) { selects[1].innerHTML = `<option value="">${escapeHtml(translatePhrase('All'))}</option>${countries.map(x => `<option value="${escapeHtml(x)}">${escapeHtml(x)}</option>`).join('')}`; selects[1].addEventListener('change', () => { window.__heyteaReviews.country = selects[1].value; renderReviewWorkbench(); }); }
      if (selects[2]) { selects[2].innerHTML = `<option value="">${escapeHtml(translatePhrase('All'))}</option>${platforms.map(x => `<option value="${escapeHtml(x)}">${escapeHtml(x)}</option>`).join('')}`; selects[2].addEventListener('change', () => { window.__heyteaReviews.platform = selects[2].value; renderReviewWorkbench(); }); }
      if (selects[3]) { selects[3].innerHTML = `<option value="">${escapeHtml(translatePhrase('All Stores'))}</option>${stores.map(x => `<option value="${escapeHtml(x)}">${escapeHtml(x)}</option>`).join('')}`; selects[3].addEventListener('change', () => { window.__heyteaReviews.store = selects[3].value; renderReviewWorkbench(); }); }
      document.getElementById('hasImage')?.addEventListener('change', event => { window.__heyteaReviews.hasImage = event.target.checked; renderReviewWorkbench(); });
      document.getElementById('hasOrder')?.addEventListener('change', event => { window.__heyteaReviews.hasOrder = event.target.checked; renderReviewWorkbench(); });
      const keyword = Array.from(document.querySelectorAll('main input[type="text"]')).find(input => (input.placeholder || '').toLowerCase().includes('hair'));
      if (keyword) keyword.addEventListener('input', () => { window.__heyteaReviews.keyword = keyword.value.trim(); renderReviewWorkbench(); });
      renderReviewWorkbench();
    } catch (error) {
      notify(`Review workbench load failed: ${error.message || error}`);
    }
  }
  document.addEventListener('DOMContentLoaded', () => {
    showLoginSplash();
    normalizeLayout(); normalizeHeader(); startClock(); applyLanguage(); initDrawer(); initFormState(); initButtons(); initClickableRows(); initSearch(); startEventPolling(); initDashboardPage(); initStoreCoveragePage(); initReviewWorkbenchPage(); initPlatformMatrixPage(); initQualityReportPage(); initSafetyAuditPage(); refreshCollectionTasksPage(true); renderSettingsPage(); initSettingsImport();
    clearInterval(window.__heyteaCollectionTimer);
    window.__heyteaCollectionTimer = setInterval(() => {
      refreshCollectionTasksPage(false).catch(() => {});
      if (pageByPath() === 'dashboard') initDashboardPage().catch(() => {});
      if (pageByPath() === 'platform_matrix') initPlatformMatrixPage().catch(() => {});
      if (pageByPath() === 'quality_report') initQualityReportPage().catch(() => {});
      if (pageByPath() === 'safety_audit') initSafetyAuditPage().catch(() => {});
    }, 10000);
    document.addEventListener('click', event => {
      if (event.target.closest('.heytea-settings-shell')) handleSettingsAction(event);
    });
  });
})();
